"""
Sora Client - Browser automation for sora.chatgpt.com video generation.

Uses Playwright to automate the Sora web interface, leveraging the user's
existing ChatGPT session for free (non-API) video generation.

Usage:
    from src.video.sora_client import SoraClient

    async with SoraClient() as sora:
        output = await sora.generate_video(
            image_path="/path/to/image.png",
            prompt="Person seated in chair, breathing naturally",
            duration=10,
            orientation="landscape",
            output_path="/path/to/output.mp4",
        )
"""

import asyncio
import os
import time
from playwright.async_api import async_playwright, Page, BrowserContext

# Default Chrome profile directory for persistent session
DEFAULT_PROFILE_DIR = os.path.expanduser("~/.cloner/sora_profile")
SORA_URL = "https://sora.chatgpt.com"

# Timeouts
NAV_TIMEOUT = 30_000         # 30s for page navigation
UPLOAD_TIMEOUT = 10_000      # 10s for file upload
GENERATION_TIMEOUT = 600_000 # 10 min max for video generation
POLL_INTERVAL = 15           # seconds between activity checks

VALID_DURATIONS = {5, 10, 15, 20}
VALID_ORIENTATIONS = {"landscape", "portrait"}

# DOM selectors discovered from live Sora UI inspection (Feb 2026)
SEL_PROMPT = '[placeholder="Describe your video..."]'
SEL_FILE_INPUT = 'input[type="file"]'
SEL_SUBMIT = 'button:has-text("Create video")'
SEL_ACTIVITY_BTN = 'button[aria-label="Activity"]'
SEL_DRAFT_READY = 'text="Your draft is ready"'
SEL_VIDEO_FAILED = 'text="Your video failed"'
SEL_DRAFT_MENU = 'button[aria-haspopup="menu"]'
SEL_DOWNLOAD = 'text="Download"'


async def _try_visible(locator, timeout_ms: int = 2000) -> bool:
    """Check if a locator becomes visible within timeout. Safe wrapper."""
    try:
        await locator.wait_for(state="visible", timeout=timeout_ms)
        return True
    except Exception:
        return False


class SoraClient:
    """Automates sora.chatgpt.com for image-to-video generation."""

    def __init__(self, profile_dir: str | None = None, headless: bool = False):
        self.profile_dir = profile_dir or DEFAULT_PROFILE_DIR
        self.headless = headless
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._pre_submit_drafts = 0
        self._pre_submit_failures = 0

    async def __aenter__(self):
        await self._launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

    async def _launch(self):
        """Launch browser with persistent profile."""
        os.makedirs(self.profile_dir, exist_ok=True)
        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            self.profile_dir,
            headless=self.headless,
            channel="chrome",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
            accept_downloads=True,
        )
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

    async def _close(self):
        """Close browser context."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()

    async def _ensure_logged_in(self):
        """Navigate to Sora and wait for a fully loaded, logged-in state."""
        page = self._page
        prompt_box = page.locator(SEL_PROMPT).first

        await page.goto(f"{SORA_URL}/explore", timeout=NAV_TIMEOUT)
        await page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT)

        # Poll until the prompt box appears. If user needs to log in
        # (OAuth, MFA, etc.), they do it in the visible browser window.
        login_timeout = 300  # 5 minutes for first-time login
        start = time.time()
        logged_in = False
        prompted_user = False

        while time.time() - start < login_timeout:
            if await _try_visible(prompt_box, 3000):
                logged_in = True
                break

            if not prompted_user and ("auth" in page.url or "login" in page.url
                                      or "accounts.google" in page.url):
                print("[SORA] Not logged in. Please complete login in the browser window.")
                print("[SORA] Waiting for you to finish login (OAuth + MFA)...")
                prompted_user = True

            await page.wait_for_timeout(3000)

            # If back on sora but not on explore, navigate there
            if "sora.chatgpt.com" in page.url and "/explore" not in page.url:
                await page.goto(f"{SORA_URL}/explore", timeout=NAV_TIMEOUT)
                await page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT)
                await page.wait_for_timeout(3000)

        if not logged_in:
            raise TimeoutError("Login timed out. Please run again — your session should be saved.")

        print("[SORA] Logged in and ready.")

    async def _configure_settings(self, duration: int, orientation: str):
        """Open settings panel and configure duration + orientation."""
        page = self._page

        # Find the Settings/model selector button near the prompt bar
        settings_btn = page.locator('button:has-text("Sora 2")').first
        if not await _try_visible(settings_btn, 2000):
            print("[SORA] Settings button not found, using defaults")
            return

        await settings_btn.click()
        await page.wait_for_timeout(500)

        # Set orientation
        target_orient = "Landscape" if orientation == "landscape" else "Portrait"
        orient_row = page.locator('text="Orientation"').first
        if await _try_visible(orient_row, 1000):
            await orient_row.click()
            await page.wait_for_timeout(300)
            orient_option = page.locator(f'text="{target_orient}"').first
            if await _try_visible(orient_option, 1000):
                await orient_option.click()
                await page.wait_for_timeout(300)

        # Set duration
        duration_row = page.locator('text="Duration"').first
        if await _try_visible(duration_row, 1000):
            await duration_row.click()
            await page.wait_for_timeout(300)
            duration_option = page.locator(f'text="{duration}s"').first
            if await _try_visible(duration_option, 1000):
                await duration_option.click()
                await page.wait_for_timeout(300)

        # Close settings by clicking the prompt box
        await page.locator(SEL_PROMPT).click()
        await page.wait_for_timeout(300)
        print(f"[SORA] Settings: {target_orient}, {duration}s")

    async def _upload_image(self, image_path: str):
        """Upload an image via the hidden file input."""
        page = self._page
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Image not found: {abs_path}")

        file_input = page.locator(SEL_FILE_INPUT).first
        await file_input.set_input_files(abs_path, timeout=UPLOAD_TIMEOUT)
        await page.wait_for_timeout(2000)
        print(f"[SORA] Uploaded image: {os.path.basename(abs_path)}")

    async def _enter_prompt(self, prompt: str):
        """Type prompt into the description field."""
        page = self._page
        text_input = page.locator(SEL_PROMPT).first
        await text_input.click()
        await text_input.fill(prompt)
        await page.wait_for_timeout(300)
        print(f"[SORA] Prompt: {prompt[:80]}...")

    async def _count_activity_items(self) -> tuple[int, int]:
        """Open Activity panel and count drafts/failures. Returns (drafts, failures)."""
        page = self._page
        panel_opened = False
        activity_btn = page.locator(SEL_ACTIVITY_BTN).first

        if await _try_visible(activity_btn, 2000):
            await activity_btn.click()
            await page.wait_for_timeout(1500)
            panel_opened = True

        drafts = await page.locator(SEL_DRAFT_READY).count()
        failures = await page.locator(SEL_VIDEO_FAILED).count()

        if panel_opened:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)

        return drafts, failures

    async def _submit(self):
        """Click the 'Create video' submit button."""
        page = self._page
        submit_btn = page.locator(SEL_SUBMIT).first

        await submit_btn.wait_for(state="visible", timeout=5000)

        # Wait for button to become enabled (needs prompt text)
        for _ in range(10):
            if await submit_btn.is_enabled():
                break
            await page.wait_for_timeout(500)
        else:
            raise RuntimeError("Submit button never became enabled")

        # Snapshot activity counts BEFORE submitting to detect new items later
        self._pre_submit_drafts, self._pre_submit_failures = await self._count_activity_items()
        print(f"[SORA] Pre-submit: {self._pre_submit_drafts} drafts, {self._pre_submit_failures} failures")

        await submit_btn.click()
        await page.wait_for_timeout(2000)
        print("[SORA] Generation submitted! Sora typically takes 2-5 minutes...")

    async def _wait_for_completion(self) -> str:
        """Poll Activity panel until a NEW draft appears. Returns draft URL."""
        page = self._page
        start_time = time.time()
        prev_drafts = self._pre_submit_drafts
        prev_failures = self._pre_submit_failures
        print("[SORA] Waiting for video generation (watching for new activity)...")

        while (time.time() - start_time) * 1000 < GENERATION_TIMEOUT:
            # Open Activity panel
            activity_btn = page.locator(SEL_ACTIVITY_BTN).first
            if await _try_visible(activity_btn, 2000):
                await activity_btn.click()
                await page.wait_for_timeout(1500)

            # Count current drafts and failures
            current_drafts = await page.locator(SEL_DRAFT_READY).count()
            current_failures = await page.locator(SEL_VIDEO_FAILED).count()

            # New draft appeared
            if current_drafts > prev_drafts:
                print(f"[SORA] New draft detected! ({prev_drafts} -> {current_drafts})")
                draft_link = page.locator(SEL_DRAFT_READY).first
                await draft_link.click()
                await page.wait_for_timeout(3000)
                await page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT)
                draft_url = page.url
                print(f"[SORA] Draft ready: {draft_url}")
                return draft_url

            # New failure appeared
            if current_failures > prev_failures:
                raise RuntimeError(
                    "Sora video generation failed — content may violate guardrails. "
                    "Try using a stylized/cartoon version of the image."
                )

            # Close activity panel and wait
            await page.keyboard.press("Escape")
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            print(f"[SORA] Still generating... ({mins}m {secs}s elapsed)")
            await page.wait_for_timeout(POLL_INTERVAL * 1000)

        raise TimeoutError(f"Sora generation timed out after {GENERATION_TIMEOUT // 1000}s")

    async def _download_video(self, output_path: str) -> str:
        """Download the video from the current draft page."""
        page = self._page

        if "/d/gen_" not in page.url:
            raise RuntimeError(f"Not on a draft page: {page.url}")

        # Find the three-dot menu button (has aria-haspopup="menu")
        # The draft page's "..." menu is the last one (sidebar Settings is earlier)
        menu_buttons = page.locator(SEL_DRAFT_MENU)
        count = await menu_buttons.count()
        three_dot = menu_buttons.nth(count - 1) if count > 1 else menu_buttons.first

        download_dir = os.path.dirname(output_path)
        os.makedirs(download_dir, exist_ok=True)

        async with page.expect_download(timeout=60_000) as download_info:
            await three_dot.click()
            await page.wait_for_timeout(500)
            download_btn = page.locator(SEL_DOWNLOAD).first
            await download_btn.click()

        download = await download_info.value
        await download.save_as(output_path)
        print(f"[SORA] Video saved: {output_path}")
        return output_path

    async def generate_video(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        duration: int = 10,
        orientation: str = "landscape",
    ) -> str:
        """
        Generate a video from an image using Sora.

        Args:
            image_path: Path to the reference image (first frame).
            prompt: Text description of the desired video motion.
            output_path: Where to save the downloaded MP4.
            duration: Video duration in seconds (5, 10, 15, 20).
            orientation: "landscape" or "portrait".

        Returns:
            Path to the saved video file.
        """
        if duration not in VALID_DURATIONS:
            raise ValueError(f"Invalid duration {duration}s. Must be one of: {sorted(VALID_DURATIONS)}")
        if orientation not in VALID_ORIENTATIONS:
            raise ValueError(f"Invalid orientation '{orientation}'. Must be one of: {sorted(VALID_ORIENTATIONS)}")

        print(f"[SORA] === Starting video generation ===")
        print(f"[SORA] Image: {image_path}")
        print(f"[SORA] Prompt: {prompt[:80]}...")
        print(f"[SORA] Duration: {duration}s, Orientation: {orientation}")

        await self._ensure_logged_in()

        # Navigate fresh to explore page for clean state
        await self._page.goto(f"{SORA_URL}/explore", timeout=NAV_TIMEOUT)
        await self._page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT)
        await self._page.wait_for_timeout(1000)

        try:
            await self._configure_settings(duration, orientation)
            await self._upload_image(image_path)
            await self._enter_prompt(prompt)
            await self._submit()
            await self._wait_for_completion()
            return await self._download_video(output_path)
        except Exception:
            # Reset to clean state on failure so next call starts fresh
            try:
                await self._page.goto(f"{SORA_URL}/explore", timeout=NAV_TIMEOUT)
            except Exception:
                pass
            raise


def generate_video_sync(
    image_path: str,
    prompt: str,
    output_path: str,
    duration: int = 10,
    orientation: str = "landscape",
    headless: bool = False,
    profile_dir: str | None = None,
) -> str:
    """
    Synchronous wrapper for SoraClient.generate_video().

    Designed to be called from background threads (e.g., clone_controller's
    daemon thread). Do NOT call from the tkinter main thread — it will block.
    """
    async def _run():
        async with SoraClient(profile_dir=profile_dir, headless=headless) as sora:
            return await sora.generate_video(
                image_path=image_path,
                prompt=prompt,
                output_path=output_path,
                duration=duration,
                orientation=orientation,
            )

    return asyncio.run(_run())
