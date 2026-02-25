"""Tests for video backend factory and Kling client interface."""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestVideoBackendFactory:
    """Test the get_video_backend factory function."""

    def test_sora_backend_returns_adapter(self):
        from src.video.video_backend import get_video_backend, SoraBackendAdapter
        backend = get_video_backend("sora")
        assert isinstance(backend, SoraBackendAdapter)

    def test_kling_backend_returns_client(self):
        """Kling backend requires FAL_KEY."""
        os.environ["FAL_KEY"] = "test_key"
        try:
            from src.video.video_backend import get_video_backend
            from src.video.kling_client import KlingClient
            config = {
                "kling": {
                    "model": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
                    "fallback_model": "fal-ai/kling-video/o1/image-to-video",
                }
            }
            backend = get_video_backend("kling", config)
            assert isinstance(backend, KlingClient)
        finally:
            del os.environ["FAL_KEY"]

    def test_unknown_backend_raises(self):
        from src.video.video_backend import get_video_backend
        with pytest.raises(ValueError, match="Unknown video backend"):
            get_video_backend("nonexistent")

    def test_kling_uses_config_model(self):
        """Kling client should use model from config."""
        os.environ["FAL_KEY"] = "test_key"
        try:
            from src.video.video_backend import get_video_backend
            config = {
                "kling": {
                    "model": "custom-model-id",
                    "fallback_model": "custom-fallback",
                }
            }
            backend = get_video_backend("kling", config)
            assert backend.model == "custom-model-id"
            assert backend.fallback_model == "custom-fallback"
        finally:
            del os.environ["FAL_KEY"]


class TestKlingClient:
    """Test KlingClient interface."""

    def test_requires_fal_key(self):
        """Should raise if FAL_KEY not set."""
        # Clear any existing FAL_KEY
        old_key = os.environ.pop("FAL_KEY", None)
        old_api_key = os.environ.pop("FAL_API_KEY", None)
        try:
            from src.video.kling_client import KlingClient
            with pytest.raises(ValueError, match="FAL_KEY"):
                KlingClient()
        finally:
            if old_key:
                os.environ["FAL_KEY"] = old_key
            if old_api_key:
                os.environ["FAL_API_KEY"] = old_api_key

    def test_accepts_fal_api_key_fallback(self):
        """Should accept FAL_API_KEY as fallback."""
        old_key = os.environ.pop("FAL_KEY", None)
        os.environ["FAL_API_KEY"] = "test_api_key"
        try:
            from src.video.kling_client import KlingClient
            client = KlingClient()
            assert os.environ["FAL_KEY"] == "test_api_key"
        finally:
            del os.environ["FAL_API_KEY"]
            if old_key:
                os.environ["FAL_KEY"] = old_key

    def test_image_to_data_url(self, tmp_path):
        """Test base64 data URL conversion."""
        os.environ["FAL_KEY"] = "test_key"
        try:
            from src.video.kling_client import KlingClient
            # Create a test image file
            test_img = tmp_path / "test.png"
            test_img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

            url = KlingClient._image_to_data_url(str(test_img))
            assert url.startswith("data:image/png;base64,")
        finally:
            del os.environ["FAL_KEY"]

    def test_generate_video_calls_fal(self, tmp_path):
        """Test that generate_video calls fal_client.subscribe."""
        os.environ["FAL_KEY"] = "test_key"
        try:
            # Mock fal_client before importing kling_client
            mock_fal = MagicMock()
            mock_result = {"video": {"url": "https://example.com/video.mp4"}}
            mock_fal.subscribe.return_value = mock_result

            with patch.dict(sys.modules, {"fal_client": mock_fal}):
                # Force reimport
                if "src.video.kling_client" in sys.modules:
                    del sys.modules["src.video.kling_client"]
                from src.video.kling_client import KlingClient

                # Create test image
                test_img = tmp_path / "test.png"
                test_img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
                output_path = str(tmp_path / "output.mp4")

                client = KlingClient()

                mock_response = MagicMock()
                mock_response.content = b"fake_video_data"

                with patch("requests.get", return_value=mock_response):
                    result = client.generate_video(
                        image_path=str(test_img),
                        prompt="Test prompt",
                        output_path=output_path,
                        duration=10,
                    )

                mock_fal.subscribe.assert_called_once()
                assert result == output_path
                assert os.path.exists(output_path)
        finally:
            del os.environ["FAL_KEY"]


class TestSoraBackendAdapter:
    """Test SoraBackendAdapter wrapping."""

    def test_has_generate_video_method(self):
        from src.video.video_backend import SoraBackendAdapter
        adapter = SoraBackendAdapter()
        assert hasattr(adapter, "generate_video")
        assert callable(adapter.generate_video)
