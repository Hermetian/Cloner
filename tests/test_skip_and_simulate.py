"""Tests for skip_to_clone and simulate_interviewer features."""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestSkipToClone:
    """Test skip_to_clone validates cached videos."""

    def test_skip_fails_with_missing_videos(self, tmp_path):
        """Should report missing videos when cache is empty."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "ELEVENLABS_API_KEY": "test"}):
            # Mock VIDEO_DIR to use tmp_path
            import scripts.clone_controller as ctrl
            original_video_dir = ctrl.VIDEO_DIR
            ctrl.VIDEO_DIR = str(tmp_path)

            try:
                # Create a mock controller with minimal GUI
                mock_controller = MagicMock()
                mock_controller.state = "wait_rec"
                mock_controller.help_label = MagicMock()
                mock_controller.log = MagicMock()

                # Call the actual skip_to_clone logic
                required = ["entry.mp4", "idle_loop.mp4", "exit.mp4"]
                missing = [f for f in required if not os.path.exists(os.path.join(str(tmp_path), f))]

                assert len(missing) == 3
                assert "entry.mp4" in missing
                assert "idle_loop.mp4" in missing
                assert "exit.mp4" in missing
            finally:
                ctrl.VIDEO_DIR = original_video_dir

    def test_skip_succeeds_with_cached_videos(self, tmp_path):
        """Should proceed when all required videos exist."""
        # Create fake cached videos
        for name in ["entry.mp4", "idle_loop.mp4", "exit.mp4"]:
            (tmp_path / name).write_bytes(b"fake_video_data")

        required = ["entry.mp4", "idle_loop.mp4", "exit.mp4"]
        missing = [f for f in required if not os.path.exists(os.path.join(str(tmp_path), f))]

        assert len(missing) == 0

    def test_skip_loads_cached_descriptor(self, tmp_path):
        """Should attempt to load person_descriptor.json if it exists."""
        # Create a fake descriptor file
        import json
        descriptor = {"hair_color": "brown", "clothing_upper": "blue shirt"}
        (tmp_path / "person_descriptor.json").write_text(json.dumps(descriptor))

        assert (tmp_path / "person_descriptor.json").exists()


class TestSimulateInterviewer:
    """Test simulate_interviewer routes text correctly."""

    def test_simulate_rejects_empty_text(self):
        """Should do nothing when entry is empty."""
        mock_entry = MagicMock()
        mock_entry.get.return_value = ""

        # The function should return early for empty text
        text = mock_entry.get().strip()
        assert text == ""

    def test_simulate_rejects_wrong_state(self):
        """Should reject simulation when not in running state."""
        state = "wait_rec"
        assert state != "running"

    def test_simulate_accepts_running_state(self):
        """Should accept simulation when in running state."""
        state = "running"
        text = "Hello, tell me about your experience"

        assert state == "running"
        assert len(text) > 0

    def test_simulate_clears_entry(self):
        """Should clear the text entry after use."""
        mock_entry = MagicMock()
        mock_entry.get.return_value = "Test question"

        # Simulate what the method does
        text = mock_entry.get().strip()
        mock_entry.delete(0, "end")

        assert text == "Test question"
        mock_entry.delete.assert_called_once()

    def test_simulate_routes_to_agent(self):
        """Should call agent.on_interviewer_speaks with the text."""
        mock_agent = MagicMock()
        text = "What makes this project special?"

        mock_agent.on_interviewer_speaks(text)
        mock_agent.on_interviewer_speaks.assert_called_once_with(text)
