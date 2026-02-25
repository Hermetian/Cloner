"""
Kling Client - Video generation via FAL API using Kling models.

Provides the same interface pattern as SoraClient but uses the FAL API
for Kling video generation (image-to-video with start/end frame interpolation).

Usage:
    from src.video.kling_client import KlingClient

    client = KlingClient(model="fal-ai/kling-video/v2.5-turbo/pro/image-to-video")
    output = client.generate_video(
        image_path="/path/to/image.png",
        prompt="Person seated in chair, breathing naturally",
        output_path="/path/to/output.mp4",
        duration=10,
    )
"""

import os
import base64
import requests


class KlingClient:
    """Generates videos using Kling models via the FAL API."""

    def __init__(self, model: str = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
                 fallback_model: str = "fal-ai/kling-video/o1/image-to-video"):
        self.model = model
        self.fallback_model = fallback_model

        # Ensure FAL_KEY is available
        fal_key = os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY", "")
        if not fal_key:
            raise ValueError("FAL_KEY environment variable not set")
        os.environ["FAL_KEY"] = fal_key

    @staticmethod
    def _image_to_data_url(path: str) -> str:
        """Convert local image to base64 data URL."""
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = path.rsplit(".", 1)[-1].lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/png")
        return f"data:{mime};base64,{data}"

    def generate_video(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        duration: int = 10,
        end_image_path: str = None,
        aspect_ratio: str = "16:9",
        orientation: str = None,
        **kwargs,
    ) -> str:
        """
        Generate a video from an image using Kling via FAL.

        Args:
            image_path: Path to the start frame image.
            prompt: Text description of the desired video motion.
            output_path: Where to save the downloaded MP4.
            duration: Video duration in seconds (5 or 10).
            end_image_path: Optional path to end frame for interpolation.
            aspect_ratio: Aspect ratio (default "16:9").

        Returns:
            Path to the saved video file.
        """
        import fal_client

        # Translate orientation to aspect_ratio if provided
        if orientation and not aspect_ratio or aspect_ratio == "16:9":
            if orientation == "portrait":
                aspect_ratio = "9:16"
            else:
                aspect_ratio = "16:9"

        print(f"[KLING] === Starting video generation ===")
        print(f"[KLING] Image: {image_path}")
        print(f"[KLING] Prompt: {prompt[:80]}...")
        print(f"[KLING] Duration: {duration}s, Model: {self.model}")

        start_url = self._image_to_data_url(image_path)

        arguments = {
            "prompt": prompt,
            "image_url": start_url,
            "duration": str(duration),
            "aspect_ratio": aspect_ratio,
        }

        # If end frame provided, use start/end interpolation
        if end_image_path:
            end_url = self._image_to_data_url(end_image_path)
            arguments["tail_image_url"] = end_url

        try:
            result = fal_client.subscribe(self.model, arguments=arguments)
        except Exception as e:
            print(f"[KLING] Primary model failed: {e}, trying fallback...")
            result = fal_client.subscribe(self.fallback_model, arguments=arguments)

        video_url = result['video']['url']

        # Download the video
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        resp = requests.get(video_url)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        print(f"[KLING] Video saved: {output_path}")
        return output_path
