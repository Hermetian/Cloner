#!/usr/bin/env python3
"""Quick webcam capture for viseme library building."""

import sys
import time
import cv2
from pathlib import Path

def capture_webcam(duration=5, output_path="data/captures/webcam_capture.mp4"):
    """Capture video from webcam."""
    print(f"Opening webcam...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return None

    # Get properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Webcam: {width}x{height} @ {fps}fps")

    # Setup output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    # Countdown
    print("\nGet ready! Recording starts in...")
    for i in range(3, 0, -1):
        ret, frame = cap.read()
        if ret:
            # Show countdown
            display = frame.copy()
            cv2.putText(display, str(i), (width//2 - 60, height//2 + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 8)
            cv2.imshow("Capture", display)
        print(f"  {i}...")
        cv2.waitKey(1000)

    print("\nRECORDING! Speak naturally with varied sounds...")
    print("(Say: 'Peter Piper picked a peck of pickled peppers')")

    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            break

        writer.write(frame)
        frame_count += 1

        # Show with recording indicator
        display = frame.copy()
        elapsed = time.time() - start_time
        remaining = duration - elapsed
        cv2.circle(display, (30, 30), 15, (0, 0, 255), -1)  # Red dot
        cv2.putText(display, f"REC {remaining:.1f}s", (55, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Capture", display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print(f"\nCaptured {frame_count} frames to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    capture_webcam(duration)
