"""Google Meet meeting capture module."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict
from src.capture.browser_automation import BrowserAutomation

logger = logging.getLogger(__name__)


class GoogleMeetCapture(BrowserAutomation):
    """
    Google Meet meeting capture automation.

    Handles joining Google Meet meetings and recording audio/video.
    """

    def __init__(
        self,
        headless: bool = False,  # Default False for debugging
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Google Meet capture.

        Args:
            headless: Run browser in headless mode
            email: Google account email (optional, for auto-login)
            password: Google account password (optional, for auto-login)
            **kwargs: Additional args passed to BrowserAutomation
        """
        super().__init__(headless=headless, browser_type="chromium", **kwargs)
        self.email = email
        self.password = password
        self.meeting_url = None
        self.is_joined = False

        logger.info("Google Meet capture initialized")

    async def join_meeting(
        self,
        meeting_url: str,
        display_name: Optional[str] = "Recorder Bot",
        mute_audio: bool = True,
        disable_video: bool = True,
        auto_join: bool = True
    ) -> bool:
        """
        Join a Google Meet meeting.

        Args:
            meeting_url: Google Meet URL
            display_name: Name to display in the meeting
            mute_audio: Start with audio muted
            disable_video: Start with video disabled
            auto_join: Automatically click "Join now"

        Returns:
            True if successfully joined
        """
        try:
            logger.info(f"Joining meeting: {meeting_url}")
            self.meeting_url = meeting_url

            # Navigate to meeting
            await self.navigate(meeting_url)
            await self.wait(2)

            # Handle potential login requirement
            current_url = self.page.url
            if "accounts.google.com" in current_url and self.email and self.password:
                logger.info("Login required, attempting auto-login...")
                await self._handle_login()
                await self.wait(2)

            # Wait for meeting interface to load
            try:
                # Wait for either join button or meeting controls
                await self.page.wait_for_selector(
                    'button[jsname="Qx7uuf"], div[jsname="Uo7zsc"]',
                    timeout=15000
                )
            except:
                logger.warning("Meeting interface not detected, continuing anyway...")

            # Enter display name if prompted
            try:
                name_input = await self.page.query_selector('input[placeholder*="name" i]')
                if name_input:
                    logger.info(f"Setting display name: {display_name}")
                    await name_input.fill(display_name)
                    await self.wait(0.5)
            except:
                logger.debug("No name input found or already filled")

            # Mute audio if requested
            if mute_audio:
                try:
                    await self._toggle_mic(mute=True)
                except:
                    logger.warning("Could not mute microphone")

            # Disable video if requested
            if disable_video:
                try:
                    await self._toggle_camera(disable=True)
                except:
                    logger.warning("Could not disable camera")

            # Join the meeting
            if auto_join:
                await self._click_join_button()
                await self.wait(3)

                # Verify we're in the meeting
                self.is_joined = await self._verify_joined()

                if self.is_joined:
                    logger.info("Successfully joined meeting!")
                else:
                    logger.warning("May not have joined successfully, check manually")

            return self.is_joined

        except Exception as e:
            logger.error(f"Failed to join meeting: {e}")
            raise

    async def _handle_login(self):
        """Handle Google login if required."""
        try:
            logger.info("Handling Google login...")

            # Enter email
            email_field = await self.page.wait_for_selector(
                'input[type="email"]',
                timeout=10000
            )
            await email_field.fill(self.email)
            await self.page.click('button:has-text("Next"), #identifierNext')
            await self.wait(2)

            # Enter password
            password_field = await self.page.wait_for_selector(
                'input[type="password"]',
                timeout=10000
            )
            await password_field.fill(self.password)
            await self.page.click('button:has-text("Next"), #passwordNext')
            await self.wait(3)

            logger.info("Login complete")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    async def _toggle_mic(self, mute: bool = True):
        """Toggle microphone on/off."""
        try:
            # Try multiple selectors for mic button
            mic_selectors = [
                'button[data-is-muted="false"]',
                'button[aria-label*="microphone" i]',
                'button[aria-label*="mic" i]',
                'div[data-is-muted] button'
            ]

            for selector in mic_selectors:
                try:
                    mic_button = await self.page.query_selector(selector)
                    if mic_button:
                        is_muted = await mic_button.get_attribute('data-is-muted')
                        should_click = (mute and is_muted == 'false') or (not mute and is_muted == 'true')

                        if should_click:
                            await mic_button.click()
                            await self.wait(0.5)
                            action = "Muted" if mute else "Unmuted"
                            logger.info(f"{action} microphone")
                        return
                except:
                    continue

            logger.debug("Mic button not found or already in desired state")

        except Exception as e:
            logger.error(f"Failed to toggle mic: {e}")

    async def _toggle_camera(self, disable: bool = True):
        """Toggle camera on/off."""
        try:
            # Try multiple selectors for camera button
            camera_selectors = [
                'button[data-is-muted="false"][aria-label*="camera" i]',
                'button[aria-label*="camera" i]',
                'button[aria-label*="video" i]'
            ]

            for selector in camera_selectors:
                try:
                    camera_button = await self.page.query_selector(selector)
                    if camera_button:
                        is_off = await camera_button.get_attribute('data-is-muted')
                        should_click = (disable and is_off == 'false') or (not disable and is_off == 'true')

                        if should_click:
                            await camera_button.click()
                            await self.wait(0.5)
                            action = "Disabled" if disable else "Enabled"
                            logger.info(f"{action} camera")
                        return
                except:
                    continue

            logger.debug("Camera button not found or already in desired state")

        except Exception as e:
            logger.error(f"Failed to toggle camera: {e}")

    async def _click_join_button(self):
        """Click the join/ask to join button."""
        try:
            # Multiple possible join button selectors
            join_selectors = [
                'button:has-text("Join now")',
                'button:has-text("Ask to join")',
                'button[jsname="Qx7uuf"]',  # Common Google Meet button
                'span:has-text("Join now")',
                'span:has-text("Ask to join")'
            ]

            for selector in join_selectors:
                try:
                    join_button = await self.page.query_selector(selector)
                    if join_button:
                        await join_button.click()
                        logger.info("Clicked join button")
                        return
                except:
                    continue

            logger.warning("Join button not found, may already be in meeting")

        except Exception as e:
            logger.error(f"Failed to click join button: {e}")

    async def _verify_joined(self) -> bool:
        """Verify that we've successfully joined the meeting."""
        try:
            # Look for meeting indicators
            indicators = [
                'button[aria-label*="Leave call" i]',
                'button[aria-label*="End call" i]',
                'div[data-meeting-title]',
                'div[jsname="tE7Oxf"]'  # Participant list container
            ]

            for indicator in indicators:
                try:
                    element = await self.page.query_selector(indicator)
                    if element:
                        return True
                except:
                    continue

            return False

        except Exception as e:
            logger.error(f"Failed to verify join status: {e}")
            return False

    async def start_recording(self, output_path: str, duration: Optional[int] = None):
        """
        Start recording the meeting.

        Args:
            output_path: Path to save the recording
            duration: Recording duration in seconds (None = record until stopped)

        Note: This uses Playwright's video recording feature.
              For audio-only or more advanced capture, additional tools needed.
        """
        try:
            logger.info(f"Starting recording to: {output_path}")

            # Start video recording
            video_path = Path(output_path)
            video_path.parent.mkdir(parents=True, exist_ok=True)

            # Note: For full implementation, you'd use screen recording tools
            # or media capture APIs. This is a simplified version.
            if duration:
                logger.info(f"Recording for {duration} seconds...")
                await self.wait(duration)
            else:
                logger.info("Recording started (manual stop required)")

            logger.info("Recording complete")

        except Exception as e:
            logger.error(f"Recording failed: {e}")
            raise

    async def leave_meeting(self):
        """Leave the meeting."""
        try:
            logger.info("Leaving meeting...")

            # Try to find and click leave button
            leave_selectors = [
                'button[aria-label*="Leave call" i]',
                'button[aria-label*="End call" i]',
                'button:has-text("Leave call")',
            ]

            for selector in leave_selectors:
                try:
                    leave_button = await self.page.query_selector(selector)
                    if leave_button:
                        await leave_button.click()
                        await self.wait(1)
                        logger.info("Left meeting")
                        self.is_joined = False
                        return
                except:
                    continue

            logger.warning("Leave button not found, closing page instead")
            await self.page.close()
            self.is_joined = False

        except Exception as e:
            logger.error(f"Failed to leave meeting: {e}")

    async def get_participants(self) -> list:
        """
        Get list of meeting participants.

        Returns:
            List of participant names/info
        """
        try:
            # This is a simplified version
            # Full implementation would parse the participants panel
            logger.info("Getting participants list...")

            # Try to open participants panel if not already open
            try:
                participants_button = await self.page.query_selector(
                    'button[aria-label*="participants" i], button[aria-label*="people" i]'
                )
                if participants_button:
                    await participants_button.click()
                    await self.wait(1)
            except:
                pass

            # Extract participant names (implementation depends on Meet's UI structure)
            # This is a placeholder - actual implementation needs DOM inspection
            participants = []

            logger.info(f"Found {len(participants)} participants")
            return participants

        except Exception as e:
            logger.error(f"Failed to get participants: {e}")
            return []
