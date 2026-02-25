"""Tests for clone_speaker.py - TTS initialization and voice listing."""

import sys
import os
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def _reload_speaker_module():
    """Force reimport of clone_speaker to pick up env changes."""
    mod_name = "clone_speaker"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    if f"scripts.{mod_name}" in sys.modules:
        del sys.modules[f"scripts.{mod_name}"]
    return importlib.import_module(mod_name)


def _reload_speaker_obs_module():
    """Force reimport of clone_speaker_obs to pick up env changes."""
    mod_name = "clone_speaker_obs"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    if f"scripts.{mod_name}" in sys.modules:
        del sys.modules[f"scripts.{mod_name}"]
    # Mock obsws_python if not installed
    if "obsws_python" not in sys.modules:
        sys.modules["obsws_python"] = MagicMock()
    return importlib.import_module(mod_name)


class TestCloneSpeakerInit:
    """Test CloneSpeaker initialization."""

    def test_requires_elevenlabs_api_key(self):
        """Should raise ValueError if ELEVENLABS_API_KEY not set."""
        old_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            os.environ["ELEVENLABS_API_KEY"] = ""
            mod = _reload_speaker_module()
            with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
                mod.CloneSpeaker()
        finally:
            if old_key:
                os.environ["ELEVENLABS_API_KEY"] = old_key

    def test_initializes_with_api_key(self):
        """Should initialize successfully with API key."""
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        try:
            mod = _reload_speaker_module()
            speaker = mod.CloneSpeaker()
            assert speaker.voice_id is not None
            assert speaker.stability == 0.5
            assert speaker.similarity_boost == 0.75
            assert speaker.is_speaking is False
        finally:
            del os.environ["ELEVENLABS_API_KEY"]

    def test_custom_voice_id(self):
        """Should accept custom voice ID."""
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        try:
            mod = _reload_speaker_module()
            speaker = mod.CloneSpeaker(voice_id="custom_voice_123")
            assert speaker.voice_id == "custom_voice_123"
        finally:
            del os.environ["ELEVENLABS_API_KEY"]

    def test_custom_settings(self):
        """Should accept custom stability and similarity."""
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        try:
            mod = _reload_speaker_module()
            speaker = mod.CloneSpeaker(stability=0.8, similarity_boost=0.9)
            assert speaker.stability == 0.8
            assert speaker.similarity_boost == 0.9
        finally:
            del os.environ["ELEVENLABS_API_KEY"]


class TestCloneSpeakerVoiceListing:
    """Test voice listing with mocked API."""

    @patch("requests.get")
    def test_list_voices_success(self, mock_get):
        """Should return list of voices from API."""
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        try:
            mod = _reload_speaker_module()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "voices": [
                    {"voice_id": "voice1", "name": "Test Voice 1"},
                    {"voice_id": "voice2", "name": "Test Voice 2"},
                ]
            }
            mock_get.return_value = mock_response

            speaker = mod.CloneSpeaker()
            voices = speaker.list_voices()

            assert len(voices) == 2
            assert voices[0]["voice_id"] == "voice1"
        finally:
            del os.environ["ELEVENLABS_API_KEY"]

    @patch("requests.get")
    def test_list_voices_failure(self, mock_get):
        """Should raise on API error."""
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        try:
            mod = _reload_speaker_module()

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_get.return_value = mock_response

            speaker = mod.CloneSpeaker()

            with pytest.raises(Exception, match="Failed to list voices"):
                speaker.list_voices()
        finally:
            del os.environ["ELEVENLABS_API_KEY"]


class TestCloneSpeakerOBSInit:
    """Test CloneSpeakerOBS initialization."""

    def test_requires_elevenlabs_api_key(self):
        """Should raise ValueError if ELEVENLABS_API_KEY not set."""
        old_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            os.environ["ELEVENLABS_API_KEY"] = ""
            mod = _reload_speaker_obs_module()
            with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
                mod.CloneSpeakerOBS()
        finally:
            if old_key:
                os.environ["ELEVENLABS_API_KEY"] = old_key

    def test_initializes_without_obs_connection(self):
        """Should initialize without connecting to OBS."""
        os.environ["ELEVENLABS_API_KEY"] = "test-key"
        try:
            mod = _reload_speaker_obs_module()
            speaker = mod.CloneSpeakerOBS()
            assert speaker.obs_client is None
            assert speaker.voice_id is not None
        finally:
            del os.environ["ELEVENLABS_API_KEY"]
