#!/usr/bin/env python3
"""
Quick test for SoraClient browser automation.

Usage:
    python scripts/test_sora.py [image_path]

If no image_path is provided, generates a text-only video (no image upload).
On first run, you'll need to log into Sora in the browser window that opens.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.video.sora_client import SoraClient

OUTPUT_DIR = os.path.expanduser("~/Projects/Cloner/data/video")


async def test_sora(image_path: str | None = None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "sora_test.mp4")

    async with SoraClient(headless=False) as sora:
        print("=== Sora Client Test ===")
        print(f"Output: {output_path}")

        await sora._ensure_logged_in()

        # Navigate to explore for clean state
        await sora._page.goto("https://sora.chatgpt.com/explore")
        await sora._page.wait_for_load_state("domcontentloaded")
        await sora._page.wait_for_timeout(1000)

        if image_path:
            print(f"Image: {image_path}")
            await sora._upload_image(image_path)

        prompt = (
            "A cozy room with a wooden chair. "
            "Warm afternoon light streams through the window. "
            "Subtle dust particles float in the air. "
            "Camera slowly pushes in."
        )
        await sora._enter_prompt(prompt)
        await sora._submit()
        draft_url = await sora._wait_for_completion()
        result = await sora._download_video(output_path)

        print(f"\n=== SUCCESS ===")
        print(f"Video saved: {result}")
        print(f"File size: {os.path.getsize(result) / 1024:.1f} KB")


if __name__ == "__main__":
    image = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        asyncio.run(test_sora(image))
    except Exception as e:
        print(f"\n=== FAILED ===")
        print(f"Error: {e}")
        sys.exit(1)
