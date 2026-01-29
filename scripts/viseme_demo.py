#!/usr/bin/env python3
"""
Viseme-based lip sync demo and CLI.

This script demonstrates the complete viseme workflow:
1. Build a viseme library from video
2. Generate TTS with viseme timing
3. Composite lip animation in real-time

Usage:
    # Build library from video
    python scripts/viseme_demo.py build --video path/to/video.mp4 --subject-id person1

    # Generate speech with viseme animation
    python scripts/viseme_demo.py speak --library data/visemes/person1 --text "Hello world" --voice-id YOUR_VOICE_ID

    # Test with synthetic demo (no API key needed)
    python scripts/viseme_demo.py demo

    # Benchmark latency
    python scripts/viseme_demo.py benchmark --text "Test message"
"""

import os
import sys
import time
import click
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.viseme import (
    PhonemeToVisemeMapper,
    TTSWithVisemes,
    VisemeLibraryBuilder,
    VisemeLibrary,
    RealtimeVisemeCompositor,
    VisemeEvent,
    VISEME_DESCRIPTIONS
)


@click.group()
def cli():
    """Viseme-based lip sync tools."""
    pass


@cli.command()
@click.option('--video', required=True, help='Path to video of subject speaking')
@click.option('--subject-id', required=True, help='Unique identifier for subject')
@click.option('--output', default=None, help='Output directory for library')
@click.option('--sample-interval', default=3, help='Sample every N frames')
def build(video, subject_id, output, sample_interval):
    """Build a viseme library from video."""
    click.echo(f"Building viseme library for '{subject_id}' from {video}")

    builder = VisemeLibraryBuilder()
    library = builder.build_from_video(
        video_path=video,
        subject_id=subject_id,
        output_path=output,
        sample_interval=sample_interval
    )

    click.echo(f"\nLibrary saved to: {library.library_path}")
    click.echo(f"Viseme categories: {len(library.templates)}")

    for vid, template in sorted(library.templates.items()):
        click.echo(f"  Viseme {vid:2d}: {len(template.images):3d} variants - {template.description}")


@cli.command()
@click.option('--library', required=True, help='Path to viseme library')
@click.option('--text', required=True, help='Text to speak')
@click.option('--voice-id', required=True, help='ElevenLabs voice ID')
@click.option('--output', default='output/viseme_video.mp4', help='Output video path')
def speak(library, text, voice_id, output):
    """Generate speech with viseme lip sync animation."""

    if not os.getenv('ELEVENLABS_API_KEY'):
        click.echo("Error: Set ELEVENLABS_API_KEY environment variable")
        return

    click.echo(f"Loading library from {library}")
    lib = VisemeLibrary.load(library)

    if lib.neutral_frame is None:
        click.echo("Error: Library has no neutral frame")
        return

    click.echo(f"Generating speech for: '{text}'")
    tts = TTSWithVisemes()

    audio_path = Path(output).with_suffix('.mp3')
    result = tts.generate_with_visemes(
        text=text,
        voice_id=voice_id,
        output_path=str(audio_path)
    )

    click.echo(f"Generated {len(result.viseme_events)} viseme events")
    click.echo(f"Audio duration: {result.audio_duration_ms}ms")

    click.echo(f"Rendering video...")
    compositor = RealtimeVisemeCompositor(lib)

    video_path = compositor.render_to_video(
        base_frame=lib.neutral_frame,
        tts_result=result,
        output_path=output,
        include_audio=True
    )

    click.echo(f"Video saved to: {video_path}")


@cli.command()
@click.option('--text', default="Hello, how are you today? This is a test of the viseme system.", help='Text to animate')
@click.option('--duration', default=3.0, help='Duration in seconds')
def demo(text, duration):
    """Run synthetic viseme demo (no API key needed)."""
    import numpy as np
    import cv2

    click.echo("Running synthetic viseme demo...")
    click.echo(f"Text: {text}")
    click.echo(f"Duration: {duration}s")

    # Create synthetic library with colored mouth shapes
    class SyntheticLibrary:
        def __init__(self):
            self.face_bbox = (150, 120, 300, 360)
            # Color-coded visemes
            self.colors = {
                0: (80, 80, 80),      # Silence - gray (closed)
                1: (0, 120, 255),     # Open mid - orange
                2: (0, 60, 255),      # Open wide - red
                6: (255, 200, 0),     # Smile/spread - cyan
                7: (255, 100, 100),   # Round/pucker - light blue
                15: (200, 200, 200),  # S/Z teeth - light gray
                21: (50, 50, 100),    # P/B/M closed - dark
            }

        def get_viseme_image(self, viseme_id, variant=0):
            # Get color or default
            color = self.colors.get(viseme_id, self.colors.get(viseme_id % 7, (100, 100, 100)))

            # Create mouth shape based on viseme type
            img = np.zeros((80, 120, 3), dtype=np.uint8)

            if viseme_id == 0 or viseme_id == 21:
                # Closed mouth - thin line
                cv2.ellipse(img, (60, 40), (40, 8), 0, 0, 360, color, -1)
            elif viseme_id in [1, 2, 3]:
                # Open mouth - ellipse
                openness = 15 + (viseme_id * 8)
                cv2.ellipse(img, (60, 40), (35, openness), 0, 0, 360, color, -1)
            elif viseme_id in [6, 11]:
                # Spread/smile - wide ellipse
                cv2.ellipse(img, (60, 40), (50, 12), 0, 0, 360, color, -1)
            elif viseme_id in [7, 8]:
                # Rounded - circle
                cv2.circle(img, (60, 40), 20, color, -1)
            else:
                # Default - medium ellipse
                cv2.ellipse(img, (60, 40), (30, 18), 0, 0, 360, color, -1)

            return img

        def get_blended_image(self, v1, v2, blend):
            img1 = self.get_viseme_image(v1)
            img2 = self.get_viseme_image(v2)
            return cv2.addWeighted(img2, 1-blend, img1, blend, 0)

    # Create base frame (face)
    base = np.full((480, 640, 3), (240, 230, 220), dtype=np.uint8)

    # Draw face shape
    cv2.ellipse(base, (320, 260), (140, 180), 0, 0, 360, (200, 190, 180), -1)

    # Eyes
    cv2.ellipse(base, (260, 200), (25, 15), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(base, (380, 200), (25, 15), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(base, (265, 200), 10, (60, 40, 20), -1)
    cv2.circle(base, (385, 200), 10, (60, 40, 20), -1)

    # Eyebrows
    cv2.line(base, (230, 170), (290, 175), (100, 80, 60), 3)
    cv2.line(base, (350, 175), (410, 170), (100, 80, 60), 3)

    # Nose
    cv2.line(base, (320, 220), (310, 280), (180, 170, 160), 2)
    cv2.line(base, (310, 280), (330, 285), (180, 170, 160), 2)

    # Generate visemes
    mapper = PhonemeToVisemeMapper()
    frames = mapper.text_to_visemes(text, duration)

    events = [
        VisemeEvent(
            viseme_id=f.viseme_id,
            start_time_ms=int(f.start_time * 1000),
            end_time_ms=int(f.end_time * 1000),
            character=""
        )
        for f in frames
    ]

    click.echo(f"\nGenerated {len(events)} viseme events:")
    for i, e in enumerate(events[:15]):
        desc = VISEME_DESCRIPTIONS.get(e.viseme_id, "?")
        click.echo(f"  {e.start_time_ms:4d}-{e.end_time_ms:4d}ms: Viseme {e.viseme_id:2d} ({desc})")
    if len(events) > 15:
        click.echo(f"  ... and {len(events) - 15} more")

    # Compositor
    library = SyntheticLibrary()
    compositor = RealtimeVisemeCompositor(library)

    click.echo("\nPlaying animation (press 'q' to quit, 'r' to restart)...")

    total_ms = int(duration * 1000)

    while True:
        for frame in compositor.generate_frames(base.copy(), events, total_ms):
            # Add text overlay
            cv2.putText(frame, text[:50], (20, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 60, 60), 1)
            cv2.putText(frame, "Press 'q' to quit, 'r' to restart", (20, 460),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

            cv2.imshow("Viseme Demo", frame)

            key = cv2.waitKey(33) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                return
            elif key == ord('r'):
                break
        else:
            # Animation finished, wait for input
            while True:
                key = cv2.waitKey(100) & 0xFF
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    return
                elif key == ord('r'):
                    break

    cv2.destroyAllWindows()


@cli.command()
@click.option('--text', default="This is a test message for benchmarking.", help='Text to benchmark')
@click.option('--iterations', default=10, help='Number of iterations')
def benchmark(text, iterations):
    """Benchmark viseme generation latency."""
    click.echo(f"Benchmarking viseme generation...")
    click.echo(f"Text: '{text}'")
    click.echo(f"Iterations: {iterations}")

    mapper = PhonemeToVisemeMapper(use_phonemizer=False)

    # Warm up
    for _ in range(3):
        mapper.text_to_visemes(text, 2.0)

    # Benchmark
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        frames = mapper.text_to_visemes(text, 2.0)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    click.echo(f"\nResults:")
    click.echo(f"  Average: {avg_time:.2f}ms")
    click.echo(f"  Min:     {min_time:.2f}ms")
    click.echo(f"  Max:     {max_time:.2f}ms")
    click.echo(f"  Frames:  {len(frames)}")

    click.echo(f"\n  This adds ~{avg_time:.1f}ms to your latency budget.")
    click.echo(f"  Viseme mapping is negligible compared to TTS/video generation.")


@cli.command()
def list_visemes():
    """List all viseme IDs with descriptions."""
    click.echo("Standard 22-viseme set:\n")

    for vid, desc in sorted(VISEME_DESCRIPTIONS.items()):
        click.echo(f"  {vid:2d}: {desc}")


@cli.command()
@click.option('--duration', default=5.0, help='Capture duration in seconds')
@click.option('--subject-id', default='webcam_capture', help='Subject identifier')
def capture_webcam(duration, subject_id):
    """Capture from webcam to build viseme library."""
    import numpy as np
    import cv2

    click.echo(f"Capturing {duration}s from webcam...")
    click.echo("Speak naturally with varied sounds/expressions.")
    click.echo("Press 'q' to stop early.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        click.echo("Error: Could not open webcam")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Output video path
    output_dir = Path("data/captures")
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / f"{subject_id}_{int(time.time())}.mp4"

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    start_time = time.time()
    frame_count = 0

    # Countdown
    for i in range(3, 0, -1):
        ret, frame = cap.read()
        if ret:
            cv2.putText(frame, str(i), (width//2 - 50, height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 0), 4)
            cv2.imshow("Capture", frame)
        cv2.waitKey(1000)

    click.echo("Recording...")

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            break

        writer.write(frame)
        frame_count += 1

        # Show progress
        elapsed = time.time() - start_time
        remaining = duration - elapsed
        cv2.putText(frame, f"Recording: {remaining:.1f}s", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    click.echo(f"\nCaptured {frame_count} frames to: {video_path}")
    click.echo(f"\nTo build library, run:")
    click.echo(f"  python scripts/viseme_demo.py build --video {video_path} --subject-id {subject_id}")


if __name__ == '__main__':
    cli()
