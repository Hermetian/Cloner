"""Base browser automation module for meeting capture."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Base class for browser automation using Playwright."""

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        user_data_dir: Optional[str] = None
    ):
        """
        Initialize browser automation.

        Args:
            headless: Run browser in headless mode
            browser_type: Browser type (chromium, firefox, webkit)
            user_data_dir: Directory for persistent browser data
        """
        self.headless = headless
        self.browser_type = browser_type
        self.user_data_dir = user_data_dir

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        logger.info(f"Browser automation initialized: {browser_type}, headless={headless}")

    async def start(self) -> Page:
        """
        Start the browser and create a new page.

        Returns:
            Page object
        """
        try:
            logger.info("Starting browser...")

            self.playwright = await async_playwright().start()

            # Get browser launcher
            if self.browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif self.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                raise ValueError(f"Unknown browser type: {self.browser_type}")

            # Launch arguments
            launch_args = {
                "headless": self.headless,
                "args": [
                    "--use-fake-ui-for-media-stream",  # Auto-grant media permissions
                    "--use-fake-device-for-media-stream",  # Use fake camera/mic
                    "--disable-blink-features=AutomationControlled",  # Hide automation
                ]
            }

            # Launch browser with persistent context if user_data_dir specified
            if self.user_data_dir:
                self.context = await browser_launcher.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    **launch_args
                )
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            else:
                self.browser = await browser_launcher.launch(**launch_args)
                self.context = await self.browser.new_context(
                    permissions=["microphone", "camera"],
                    viewport={"width": 1920, "height": 1080}
                )
                self.page = await self.context.new_page()

            logger.info("Browser started successfully")
            return self.page

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    async def stop(self):
        """Stop the browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            logger.info("Browser stopped")

        except Exception as e:
            logger.error(f"Error stopping browser: {e}")

    async def navigate(self, url: str, wait_until: str = "networkidle"):
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
        """
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=60000)
            logger.info("Navigation complete")

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 30000,
        state: str = "visible"
    ):
        """
        Wait for an element to appear.

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            state: Element state to wait for
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            logger.debug(f"Element found: {selector}")

        except Exception as e:
            logger.error(f"Element not found: {selector}")
            raise

    async def click(self, selector: str, timeout: int = 30000):
        """
        Click an element.

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
        """
        try:
            await self.page.click(selector, timeout=timeout)
            logger.debug(f"Clicked: {selector}")

        except Exception as e:
            logger.error(f"Click failed: {selector}")
            raise

    async def type_text(self, selector: str, text: str, timeout: int = 30000):
        """
        Type text into an input field.

        Args:
            selector: CSS selector
            text: Text to type
            timeout: Timeout in milliseconds
        """
        try:
            await self.page.fill(selector, text, timeout=timeout)
            logger.debug(f"Typed text into: {selector}")

        except Exception as e:
            logger.error(f"Type failed: {selector}")
            raise

    async def screenshot(self, path: str, full_page: bool = False):
        """
        Take a screenshot.

        Args:
            path: Output file path
            full_page: Capture full scrollable page
        """
        try:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            await self.page.screenshot(path=str(output_path), full_page=full_page)
            logger.info(f"Screenshot saved: {output_path}")

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise

    async def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in the page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of the script execution
        """
        try:
            result = await self.page.evaluate(script)
            return result

        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            raise

    async def grant_permissions(self, permissions: list):
        """
        Grant specific permissions to the page.

        Args:
            permissions: List of permissions (e.g., ['microphone', 'camera'])
        """
        try:
            await self.context.grant_permissions(permissions)
            logger.info(f"Granted permissions: {permissions}")

        except Exception as e:
            logger.error(f"Failed to grant permissions: {e}")
            raise

    async def wait(self, seconds: float):
        """
        Wait for a specified duration.

        Args:
            seconds: Duration to wait in seconds
        """
        await asyncio.sleep(seconds)
        logger.debug(f"Waited {seconds} seconds")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        asyncio.run(self.stop())

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
