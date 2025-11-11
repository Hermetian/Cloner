"""Meeting recording utilities using FFmpeg and system tools."""

import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MeetingRecorder:
    """
    Handle screen and audio recording for meetings.

    Uses FFmpeg and system tools for capture.
    """

    def __init__(self, output_dir: str = "data/video"):
        """
        Initialize meeting recorder.

        Args:
            output_dir: Directory to save recordings
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.recording_process = None
        self.is_recording = False
        self.output_file = None

        logger.info(f"Meeting recorder initialized: {output_dir}")

    def start_screen_recording(
        self,
        output_filename: Optional[str] = None,
        include_audio: bool = True,
        fps: int = 30
    ) -> str:
        """
        Start screen recording using FFmpeg.

        Args:
            output_filename: Output file name (auto-generated if None)
            include_audio: Include system audio
            fps: Frames per second

        Returns:
            Path to output file

        Note: This is a simplified implementation. Full implementation would
              need platform-specific capture methods (X11, Windows, macOS).
        """
        try:
            if self.is_recording:
                logger.warning("Already recording")
                return self.output_file

            # Generate filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"meeting_{timestamp}.mp4"

            self.output_file = str(self.output_dir / output_filename)

            logger.info(f"Starting screen recording: {self.output_file}")

            # Platform-specific FFmpeg command
            # This is a template - actual implementation needs platform detection
            # For Linux/X11:
            # ffmpeg_cmd = [
            #     "ffmpeg",
            #     "-video_size", "1920x1080",
            #     "-framerate", str(fps),
            #     "-f", "x11grab",
            #     "-i", ":0.0",
            #     "-f", "pulse",
            #     "-i", "default",
            #     "-c:v", "libx264",
            #     "-preset", "ultrafast",
            #     "-c:a", "aac",
            #     self.output_file
            # ]

            # For now, return a placeholder
            logger.warning(
                "Screen recording not yet implemented. "
                "Use OBS Studio or similar tool for actual recording."
            )

            self.is_recording = True
            return self.output_file

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise

    def stop_recording(self):
        """Stop the current recording."""
        try:
            if not self.is_recording:
                logger.warning("Not currently recording")
                return

            logger.info("Stopping recording...")

            if self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=5)

            self.is_recording = False
            logger.info(f"Recording saved: {self.output_file}")

            return self.output_file

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            raise

    @staticmethod
    def check_ffmpeg_installed() -> bool:
        """Check if FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0

        except:
            return False


class ScreenshotCapture:
    """Utility for taking screenshots during meetings."""

    def __init__(self, output_dir: str = "data/video/screenshots"):
        """
        Initialize screenshot capture.

        Args:
            output_dir: Directory to save screenshots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Screenshot capture initialized: {output_dir}")

    async def capture(
        self,
        page,
        filename: Optional[str] = None,
        full_page: bool = False
    ) -> str:
        """
        Capture a screenshot using Playwright page.

        Args:
            page: Playwright page object
            filename: Output filename (auto-generated if None)
            full_page: Capture full scrollable page

        Returns:
            Path to screenshot file
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"

            output_path = self.output_dir / filename

            await page.screenshot(path=str(output_path), full_page=full_page)

            logger.info(f"Screenshot captured: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise

    async def capture_multiple(
        self,
        page,
        count: int = 5,
        interval: float = 2.0
    ) -> list:
        """
        Capture multiple screenshots at intervals.

        Args:
            page: Playwright page object
            count: Number of screenshots to capture
            interval: Interval between screenshots in seconds

        Returns:
            List of screenshot file paths
        """
        screenshots = []

        for i in range(count):
            filename = f"frame_{i+1:03d}.png"
            screenshot_path = await self.capture(page, filename)
            screenshots.append(screenshot_path)

            if i < count - 1:
                await asyncio.sleep(interval)

        logger.info(f"Captured {len(screenshots)} screenshots")
        return screenshots
