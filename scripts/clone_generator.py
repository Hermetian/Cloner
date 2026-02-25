#!/usr/bin/env python3
"""
Clone Video Generator Pipeline

1. Takes interviewee face image
2. Generates end frame (your room + clone seated)
3. Generates video sequence (entry, thinking, speaking, exit)

Uses Kling video generation via FAL API.
"""

import os
import sys
import base64
import requests
from pathlib import Path

# Load environment
from dotenv import load_dotenv
_master_env = Path.home() / "iCloudDrive" / "Documents" / "Projects" / "ClaudeCommander" / "master.env"
if _master_env.exists():
    load_dotenv(_master_env)
else:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Config
FAL_KEY = os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")
if not FAL_KEY:
    raise ValueError("FAL_KEY environment variable not set")
os.environ["FAL_KEY"] = FAL_KEY

import fal_client

# Load config for model and output paths
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
try:
    from src.utils.config_loader import ConfigLoader
    _config = ConfigLoader(str(_project_root / "config" / "config.yaml"))
    KLING_MODEL = _config.get("video_backend", "kling", "fallback_model",
                              default="fal-ai/kling-video/o1/image-to-video")
    OUTPUT_DIR = _config.get("paths", "video_dir", default=str(Path.home() / "clone_videos"))
except Exception:
    KLING_MODEL = "fal-ai/kling-video/o1/image-to-video"
    OUTPUT_DIR = str(Path.home() / "clone_videos")

ROOM_IMAGE = str(Path.home() / "webcam_reference.png")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def image_to_data_url(path):
    """Convert local image to base64 data URL."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.split(".")[-1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


def download_image(url, output_path):
    """Download image from URL."""
    resp = requests.get(url)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    print(f"  Downloaded: {output_path}")
    return output_path


def generate_end_frame(interviewee_face_path, room_image_path):
    """Generate end frame: your room with clone (interviewee's face) seated."""
    print("\n[1/5] Generating end frame with clone...")

    room_url = image_to_data_url(room_image_path)
    face_url = image_to_data_url(interviewee_face_path)

    print("  Generating scene composition...")
    result = fal_client.subscribe(
        "fal-ai/flux-pro/v1.1",
        arguments={
            "prompt": """Wide angle shot of a home office. Yellow walls, white door visible on left side.
A bald man with beard wearing olive green t-shirt and headphones sits at desk on right, facing camera.
Another man in business casual sits in chair on left side of frame, facing camera, as if on video call.
Natural lighting, photorealistic, same perspective as a webcam mounted on monitor.""",
            "image_size": "landscape_16_9",
            "num_images": 1,
        },
    )

    scene_url = result['images'][0]['url']
    scene_path = os.path.join(OUTPUT_DIR, "scene_base.jpg")
    download_image(scene_url, scene_path)

    print("  Applying face swap...")
    result = fal_client.subscribe(
        "fal-ai/face-swap",
        arguments={
            "base_image_url": scene_url,
            "swap_image_url": face_url,
        },
    )

    end_frame_url = result['image']['url']
    end_frame_path = os.path.join(OUTPUT_DIR, "end_frame.jpg")
    download_image(end_frame_url, end_frame_path)

    print(f"  End frame ready: {end_frame_path}")
    return end_frame_path


def generate_start_frame(room_image_path):
    """Generate start frame: your room with door, no clone."""
    print("\n[2/5] Preparing start frame...")

    start_frame_path = os.path.join(OUTPUT_DIR, "start_frame.png")

    import shutil
    shutil.copy(room_image_path, start_frame_path)
    print(f"  Start frame ready: {start_frame_path}")
    return start_frame_path


def generate_video(name, start_frame_path, end_frame_path, prompt, duration=5):
    """Generate video using Kling (start + end frame interpolation)."""
    print(f"\n  Generating {name} video ({duration}s)...")

    start_url = image_to_data_url(start_frame_path)
    end_url = image_to_data_url(end_frame_path)

    result = fal_client.subscribe(
        KLING_MODEL,
        arguments={
            "prompt": prompt,
            "start_image_url": start_url,
            "end_image_url": end_url,
            "duration": str(duration),
            "aspect_ratio": "16:9",
        },
    )

    video_url = result['video']['url']
    video_path = os.path.join(OUTPUT_DIR, f"{name}.mp4")
    download_image(video_url, video_path)

    print(f"  Video ready: {video_path}")
    return video_path


def generate_entry_video(start_frame_path, end_frame_path):
    """Clone enters through door, walks to seat, sits down."""
    print("\n[3/5] Generating ENTRY video...")
    return generate_video(
        "entry",
        start_frame_path,
        end_frame_path,
        "Door on left opens slowly. A man enters through the door, walks calmly across the room, "
        "and sits down in the chair on the left side. Natural walking motion, door closes behind him. "
        "Smooth camera, no cuts.",
        duration=10
    )


def generate_thinking_video(end_frame_path):
    """Clone sits and thinks, subtle movement, loops seamlessly."""
    print("\n[4/5] Generating THINKING LOOP video...")
    return generate_video(
        "thinking",
        end_frame_path,
        end_frame_path,
        "Man on left sits calmly, slight subtle movement, looks thoughtful. "
        "Minimal head movement, natural breathing motion. Seamless loop.",
        duration=5
    )


def generate_speaking_video(end_frame_path):
    """Clone speaks for lip sync."""
    print("\n[4b/5] Generating SPEAKING video...")
    return generate_video(
        "speaking",
        end_frame_path,
        end_frame_path,
        "Man on left speaks animatedly, mouth moving naturally as if talking. "
        "Natural head movement while speaking, engaged expression. Hand gestures.",
        duration=5
    )


def generate_exit_video(end_frame_path, start_frame_path):
    """Clone stands up, walks out, closes door."""
    print("\n[5/5] Generating EXIT video...")
    return generate_video(
        "exit",
        end_frame_path,
        start_frame_path,
        "Man on left stands up from chair, walks across room toward the door on left. "
        "Opens door, exits, door closes behind him. Smooth natural movement.",
        duration=10
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python clone_generator.py <interviewee_face_image>")
        print("\nThis will generate:")
        print("  1. End frame (your room + clone)")
        print("  2. Entry video (10s)")
        print("  3. Thinking loop (5s)")
        print("  4. Speaking video (5s)")
        print("  5. Exit video (10s)")
        sys.exit(1)

    interviewee_face = sys.argv[1]

    if not os.path.exists(interviewee_face):
        print(f"Error: Face image not found: {interviewee_face}")
        sys.exit(1)

    ensure_output_dir()

    print("="*50)
    print("CLONE VIDEO GENERATOR")
    print("="*50)
    print(f"Interviewee face: {interviewee_face}")
    print(f"Room reference: {ROOM_IMAGE}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("="*50)

    start_frame = generate_start_frame(ROOM_IMAGE)
    end_frame = generate_end_frame(interviewee_face, ROOM_IMAGE)

    entry_video = generate_entry_video(start_frame, end_frame)
    thinking_video = generate_thinking_video(end_frame)
    speaking_video = generate_speaking_video(end_frame)
    exit_video = generate_exit_video(end_frame, start_frame)

    print("\n" + "="*50)
    print("COMPLETE!")
    print("="*50)
    print(f"Videos saved to: {OUTPUT_DIR}")
    print(f"  - entry.mp4")
    print(f"  - thinking.mp4")
    print(f"  - speaking.mp4")
    print(f"  - exit.mp4")

if __name__ == "__main__":
    main()
