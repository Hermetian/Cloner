#!/usr/bin/env python3
"""CLI tool for capturing Google Meet and Zoom meetings."""

import sys
import asyncio
import click
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

from src.capture.google_meet_capture import GoogleMeetCapture
from src.capture.meeting_recorder import ScreenshotCapture
from src.utils.logger import setup_logger

logger = setup_logger("capture_meeting", level="INFO", console=True)


@click.group()
def cli():
    """Meeting capture CLI tool."""
    pass


@cli.command()
@click.option("--url", required=True, help="Google Meet URL")
@click.option("--duration", type=int, help="Recording duration in seconds (optional)")
@click.option("--name", default="Recorder Bot", help="Display name in meeting")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
@click.option("--mute-audio/--no-mute-audio", default=True, help="Mute microphone")
@click.option("--disable-video/--enable-video", default=True, help="Disable camera")
@click.option("--output-dir", default="data/video", help="Output directory")
@click.option("--screenshots", type=int, help="Number of screenshots to capture")
def google_meet(url, duration, name, headless, mute_audio, disable_video, output_dir, screenshots):
    """
    Join and observe a Google Meet meeting.

    This will join the meeting and optionally take screenshots.
    Use external recording software (OBS, etc.) for full recording.
    """
    asyncio.run(_capture_google_meet(
        url, duration, name, headless, mute_audio, disable_video, output_dir, screenshots
    ))


async def _capture_google_meet(
    url, duration, name, headless, mute_audio, disable_video, output_dir, screenshots
):
    """Async implementation of Google Meet capture."""
    try:
        click.echo(f"Joining Google Meet: {url}")
        click.echo(f"Display name: {name}")
        click.echo(f"Headless mode: {headless}")
        click.echo()

        # Create capture instance
        capture = GoogleMeetCapture(headless=headless)

        # Start browser
        await capture.start()

        click.echo("Browser started, joining meeting...")

        # Join meeting
        joined = await capture.join_meeting(
            meeting_url=url,
            display_name=name,
            mute_audio=mute_audio,
            disable_video=disable_video,
            auto_join=True
        )

        if not joined:
            click.echo("⚠ Warning: May not have joined successfully", err=True)
            click.echo("   Check the browser window to verify", err=True)

        click.echo("✓ Joined meeting!")
        click.echo()

        # Take screenshots if requested
        if screenshots:
            click.echo(f"Taking {screenshots} screenshots...")
            screenshot_capture = ScreenshotCapture(f"{output_dir}/screenshots")

            screenshot_paths = await screenshot_capture.capture_multiple(
                capture.page,
                count=screenshots,
                interval=2.0
            )

            click.echo("✓ Screenshots captured:")
            for path in screenshot_paths:
                click.echo(f"  • {path}")
            click.echo()

        # Wait for duration or until interrupted
        if duration:
            click.echo(f"Staying in meeting for {duration} seconds...")
            click.echo("(Press Ctrl+C to leave early)")
            try:
                await asyncio.sleep(duration)
            except KeyboardInterrupt:
                click.echo("\nInterrupted by user")
        else:
            click.echo("In meeting. Press Ctrl+C to leave.")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                click.echo("\nLeaving meeting...")

        # Leave meeting
        await capture.leave_meeting()
        click.echo("✓ Left meeting")

        # Stop browser
        await capture.stop()
        click.echo("✓ Browser closed")

    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user. Cleaning up...")
        try:
            await capture.leave_meeting()
            await capture.stop()
        except:
            pass

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--url", required=True, help="Meeting URL (Google Meet)")
@click.option("--output", "-o", required=True, help="Output screenshot file")
@click.option("--headless/--no-headless", default=False, help="Run in headless mode")
def screenshot(url, output, headless):
    """Take a single screenshot of a meeting."""
    asyncio.run(_take_screenshot(url, output, headless))


async def _take_screenshot(url, output, headless):
    """Async implementation of screenshot capture."""
    try:
        click.echo(f"Joining meeting: {url}")

        capture = GoogleMeetCapture(headless=headless)
        await capture.start()

        await capture.join_meeting(url, display_name="Screenshot Bot")

        click.echo("Taking screenshot...")
        await capture.wait(2)

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        await capture.screenshot(str(output_path))

        click.echo(f"✓ Screenshot saved: {output_path}")

        await capture.leave_meeting()
        await capture.stop()

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--url", required=True, help="Google Meet URL")
@click.option("--duration", type=int, default=60, help="Observation duration in seconds")
@click.option("--headless/--no-headless", default=False, help="Run in headless mode")
def observe(url, duration, headless):
    """
    Silently observe a meeting without joining.

    Useful for testing and meeting validation.
    """
    asyncio.run(_observe_meeting(url, duration, headless))


async def _observe_meeting(url, duration, headless):
    """Async implementation of meeting observation."""
    try:
        click.echo(f"Observing meeting: {url}")
        click.echo(f"Duration: {duration} seconds")
        click.echo()

        capture = GoogleMeetCapture(headless=headless)
        await capture.start()

        # Navigate but don't join
        await capture.navigate(url)
        await capture.wait(3)

        click.echo("Observing meeting (not joined)...")

        # Take periodic screenshots
        screenshot_capture = ScreenshotCapture("data/video/observation")

        for i in range(3):
            await screenshot_capture.capture(capture.page, f"observe_{i+1}.png")
            if i < 2:
                await asyncio.sleep(duration / 3)

        click.echo("✓ Observation complete")

        await capture.stop()

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def test():
    """Test browser automation setup."""
    asyncio.run(_test_browser())


async def _test_browser():
    """Test browser automation."""
    try:
        click.echo("Testing browser automation...")

        from src.capture.browser_automation import BrowserAutomation

        browser = BrowserAutomation(headless=False)
        await browser.start()

        click.echo("✓ Browser started")

        await browser.navigate("https://www.google.com")
        click.echo("✓ Navigation works")

        await browser.wait(2)

        await browser.stop()
        click.echo("✓ Browser stopped")

        click.echo()
        click.echo("All tests passed! ✓")

    except Exception as e:
        click.echo(f"✗ Test failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
