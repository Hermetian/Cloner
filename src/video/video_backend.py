"""
Video Backend Factory - Selects Sora or Kling based on configuration.

Usage:
    from src.video.video_backend import get_video_backend

    backend = get_video_backend("sora")
    backend.generate_video(image_path=..., prompt=..., output_path=..., duration=10)
"""


def get_video_backend(backend_name: str, config: dict = None):
    """
    Factory function to create the appropriate video generation backend.

    Args:
        backend_name: "sora" or "kling"
        config: Optional config dict with backend-specific settings

    Returns:
        A video backend instance with a generate_video() method.
    """
    config = config or {}

    if backend_name == "sora":
        return SoraBackendAdapter()

    elif backend_name == "kling":
        from src.video.kling_client import KlingClient
        kling_config = config.get("kling", {})
        model = kling_config.get("model", "fal-ai/kling-video/v2.5-turbo/pro/image-to-video")
        fallback = kling_config.get("fallback_model", "fal-ai/kling-video/o1/image-to-video")
        return KlingClient(model=model, fallback_model=fallback)

    else:
        raise ValueError(f"Unknown video backend: '{backend_name}'. Must be 'sora' or 'kling'.")


class SoraBackendAdapter:
    """Wraps SoraClient's async API to match the sync generate_video() interface."""

    def generate_video(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        duration: int = 10,
        orientation: str = "landscape",
        **kwargs,
    ) -> str:
        """Generate video using Sora (synchronous wrapper)."""
        from src.video.sora_client import generate_video_sync
        return generate_video_sync(
            image_path=image_path,
            prompt=prompt,
            output_path=output_path,
            duration=duration,
            orientation=orientation,
        )
