"""Tests for ConfigLoader with new config sections and path expansion."""

import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def config_yaml(tmp_path):
    """Create a test config.yaml with all new sections."""
    config_content = """
capture:
  browser: chromium

audio:
  mic_device: "USB CAMERA"
  capture_device: "CABLE Output (VB-Audio Virtual Cable)"
  preferred_sample_rate: 48000

obs:
  host: localhost
  port: 4455
  password: testpass

paths:
  video_dir: ~/clone_videos
  lock_file: ~/.cloner/clone_controller.lock
  env_file: ~/some/path/master.env

brain:
  model: "gpt-5.1"
  fallback_model: "gpt-4o"
  system_prompt_file: config/clone_system_prompt.txt
  max_history: 20

video_backend:
  default: sora
  kling:
    model: "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
    fallback_model: "fal-ai/kling-video/o1/image-to-video"

tts:
  voice_id: nf18MnSL81anCHgQgL1A
  silence_threshold: 500
  speech_timeout: 0.8
  min_speech_duration: 0.5
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def config_loader(config_yaml):
    """Create a ConfigLoader instance from test config."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.utils.config_loader import ConfigLoader
    return ConfigLoader(config_yaml)


class TestConfigLoading:
    """Test that new config sections load correctly."""

    def test_audio_section_loads(self, config_loader):
        assert config_loader.get("audio", "mic_device") == "USB CAMERA"
        assert config_loader.get("audio", "preferred_sample_rate") == 48000

    def test_obs_section_loads(self, config_loader):
        assert config_loader.get("obs", "host") == "localhost"
        assert config_loader.get("obs", "port") == 4455
        assert config_loader.get("obs", "password") == "testpass"

    def test_brain_section_loads(self, config_loader):
        assert config_loader.get("brain", "model") == "gpt-5.1"
        assert config_loader.get("brain", "fallback_model") == "gpt-4o"
        assert config_loader.get("brain", "max_history") == 20

    def test_video_backend_section_loads(self, config_loader):
        assert config_loader.get("video_backend", "default") == "sora"
        assert config_loader.get("video_backend", "kling", "model") == "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"

    def test_tts_section_loads(self, config_loader):
        assert config_loader.get("tts", "voice_id") == "nf18MnSL81anCHgQgL1A"
        assert config_loader.get("tts", "silence_threshold") == 500
        assert config_loader.get("tts", "speech_timeout") == 0.8

    def test_get_section(self, config_loader):
        audio = config_loader.get_section("audio")
        assert isinstance(audio, dict)
        assert "mic_device" in audio
        assert "capture_device" in audio

    def test_default_on_missing_key(self, config_loader):
        assert config_loader.get("nonexistent", "key", default="fallback") == "fallback"


class TestPathExpansion:
    """Test that ~ paths are expanded correctly."""

    def test_video_dir_expanded(self, config_loader):
        video_dir = config_loader.get("paths", "video_dir")
        assert "~" not in video_dir
        assert video_dir == str(Path.home() / "clone_videos")

    def test_lock_file_expanded(self, config_loader):
        lock_file = config_loader.get("paths", "lock_file")
        assert "~" not in lock_file
        assert lock_file == str(Path.home() / ".cloner" / "clone_controller.lock")

    def test_env_file_expanded(self, config_loader):
        env_file = config_loader.get("paths", "env_file")
        assert "~" not in env_file
        assert str(Path.home()) in env_file

    def test_non_path_strings_unchanged(self, config_loader):
        """Strings without ~ should not be modified."""
        assert config_loader.get("obs", "host") == "localhost"
        assert config_loader.get("audio", "mic_device") == "USB CAMERA"


class TestEnvVarSubstitution:
    """Test environment variable substitution still works."""

    def test_env_var_placeholder(self, tmp_path):
        """Test that ${VAR} placeholders are replaced."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from src.utils.config_loader import ConfigLoader

        os.environ["TEST_API_KEY"] = "test_key_123"

        config_content = """
voice:
  api_key: "${TEST_API_KEY}"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        loader = ConfigLoader(str(config_file))
        assert loader.get("voice", "api_key") == "test_key_123"

        del os.environ["TEST_API_KEY"]
