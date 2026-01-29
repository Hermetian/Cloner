"""
Viseme library builder and manager.

Extracts mouth regions from video frames and organizes them
by viseme type for real-time compositing.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import cv2

try:
    import mediapipe as mp
    # Check for legacy vs new API
    if hasattr(mp, 'solutions'):
        HAS_MEDIAPIPE = True
        MEDIAPIPE_LEGACY = True
    elif hasattr(mp, 'tasks'):
        HAS_MEDIAPIPE = True
        MEDIAPIPE_LEGACY = False
    else:
        HAS_MEDIAPIPE = False
        MEDIAPIPE_LEGACY = False
except ImportError:
    HAS_MEDIAPIPE = False
    MEDIAPIPE_LEGACY = False
    print("Warning: mediapipe not installed. Face detection will be limited.")

from .phoneme_mapper import VISEME_MAP, VISEME_DESCRIPTIONS

logger = logging.getLogger(__name__)


@dataclass
class MouthRegion:
    """A cropped mouth region with metadata."""
    image: np.ndarray  # BGR image
    bbox: Tuple[int, int, int, int]  # x, y, w, h in original frame
    landmarks: Optional[List[Tuple[int, int]]] = None  # Lip landmarks
    frame_index: int = 0

    def save(self, path: str):
        """Save mouth region image."""
        cv2.imwrite(path, self.image)

    @classmethod
    def load(cls, path: str) -> "MouthRegion":
        """Load mouth region from file."""
        img = cv2.imread(path)
        return cls(image=img, bbox=(0, 0, img.shape[1], img.shape[0]))


@dataclass
class VisemeTemplate:
    """Template images for a single viseme."""
    viseme_id: int
    images: List[np.ndarray]  # Multiple variants
    description: str
    average_image: Optional[np.ndarray] = None

    def compute_average(self):
        """Compute average image from variants."""
        if not self.images:
            return
        # Resize all to same size and average
        target_size = self.images[0].shape[:2]
        resized = []
        for img in self.images:
            if img.shape[:2] != target_size:
                img = cv2.resize(img, (target_size[1], target_size[0]))
            resized.append(img.astype(np.float32))
        self.average_image = np.mean(resized, axis=0).astype(np.uint8)


class VisemeLibrary:
    """
    Collection of viseme templates for a specific subject.

    Can be used for real-time lip animation by selecting
    appropriate mouth images based on viseme sequence.
    """

    def __init__(self, subject_id: str, library_path: Optional[str] = None):
        """
        Initialize viseme library.

        Args:
            subject_id: Unique identifier for the subject
            library_path: Path to library directory (default: data/visemes/{subject_id})
        """
        self.subject_id = subject_id
        self.library_path = Path(library_path or f"data/visemes/{subject_id}")
        self.templates: Dict[int, VisemeTemplate] = {}
        self.neutral_frame: Optional[np.ndarray] = None
        self.face_bbox: Optional[Tuple[int, int, int, int]] = None

    def add_viseme(self, viseme_id: int, mouth_image: np.ndarray):
        """Add a mouth image to a viseme template."""
        if viseme_id not in self.templates:
            self.templates[viseme_id] = VisemeTemplate(
                viseme_id=viseme_id,
                images=[],
                description=VISEME_DESCRIPTIONS.get(viseme_id, f"Viseme {viseme_id}")
            )
        self.templates[viseme_id].images.append(mouth_image)

    def get_viseme_image(
        self,
        viseme_id: int,
        variant: int = 0
    ) -> Optional[np.ndarray]:
        """
        Get mouth image for a viseme.

        Args:
            viseme_id: Viseme ID (0-21)
            variant: Which variant to use (for natural variation)

        Returns:
            Mouth image or None if not available
        """
        template = self.templates.get(viseme_id)
        if not template or not template.images:
            # Fall back to neutral (viseme 0)
            template = self.templates.get(0)
            if not template or not template.images:
                return None

        idx = variant % len(template.images)
        return template.images[idx]

    def get_blended_image(
        self,
        viseme_id: int,
        prev_viseme_id: int,
        blend_factor: float
    ) -> Optional[np.ndarray]:
        """
        Get blended image between two visemes.

        Args:
            viseme_id: Target viseme ID
            prev_viseme_id: Previous viseme ID
            blend_factor: 0.0 = prev, 1.0 = current

        Returns:
            Blended mouth image
        """
        curr_img = self.get_viseme_image(viseme_id)
        prev_img = self.get_viseme_image(prev_viseme_id)

        if curr_img is None:
            return prev_img
        if prev_img is None:
            return curr_img

        # Ensure same size
        if curr_img.shape != prev_img.shape:
            prev_img = cv2.resize(prev_img, (curr_img.shape[1], curr_img.shape[0]))

        # Blend
        blended = cv2.addWeighted(
            prev_img, 1.0 - blend_factor,
            curr_img, blend_factor,
            0
        )
        return blended

    def save(self):
        """Save library to disk."""
        self.library_path.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            "subject_id": self.subject_id,
            "visemes": {}
        }

        for viseme_id, template in self.templates.items():
            viseme_dir = self.library_path / f"viseme_{viseme_id:02d}"
            viseme_dir.mkdir(exist_ok=True)

            # Compute average if not done
            if template.average_image is None:
                template.compute_average()

            # Save images
            image_paths = []
            for i, img in enumerate(template.images):
                path = viseme_dir / f"variant_{i:03d}.png"
                cv2.imwrite(str(path), img)
                image_paths.append(str(path.relative_to(self.library_path)))

            if template.average_image is not None:
                avg_path = viseme_dir / "average.png"
                cv2.imwrite(str(avg_path), template.average_image)

            metadata["visemes"][str(viseme_id)] = {
                "description": template.description,
                "image_count": len(template.images),
                "images": image_paths
            }

        # Save neutral frame if available
        if self.neutral_frame is not None:
            cv2.imwrite(str(self.library_path / "neutral.png"), self.neutral_frame)
            metadata["neutral_frame"] = "neutral.png"

        # Save face bbox (convert numpy ints to Python ints)
        if self.face_bbox:
            metadata["face_bbox"] = [int(x) for x in self.face_bbox]

        with open(self.library_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved viseme library to {self.library_path}")

    @classmethod
    def load(cls, library_path: str) -> "VisemeLibrary":
        """Load library from disk."""
        library_path = Path(library_path)

        with open(library_path / "metadata.json", 'r') as f:
            metadata = json.load(f)

        library = cls(
            subject_id=metadata["subject_id"],
            library_path=str(library_path)
        )

        # Load visemes
        for viseme_id_str, info in metadata["visemes"].items():
            viseme_id = int(viseme_id_str)
            library.templates[viseme_id] = VisemeTemplate(
                viseme_id=viseme_id,
                images=[],
                description=info["description"]
            )

            for img_path in info["images"]:
                full_path = library_path / img_path
                if full_path.exists():
                    img = cv2.imread(str(full_path))
                    library.templates[viseme_id].images.append(img)

            # Load average
            avg_path = library_path / f"viseme_{viseme_id:02d}" / "average.png"
            if avg_path.exists():
                library.templates[viseme_id].average_image = cv2.imread(str(avg_path))

        # Load neutral frame
        if "neutral_frame" in metadata:
            neutral_path = library_path / metadata["neutral_frame"]
            if neutral_path.exists():
                library.neutral_frame = cv2.imread(str(neutral_path))

        # Load face bbox
        if "face_bbox" in metadata:
            library.face_bbox = tuple(metadata["face_bbox"])

        logger.info(f"Loaded viseme library with {len(library.templates)} visemes")
        return library


class VisemeLibraryBuilder:
    """
    Builds a viseme library from video of a subject speaking.

    Workflow:
    1. Load video of subject speaking (ideally with varied phonemes)
    2. Detect face and extract mouth region per frame
    3. Classify or manually assign visemes to frames
    4. Build library with multiple variants per viseme
    """

    # Mouth landmark indices for MediaPipe Face Mesh
    MOUTH_LANDMARKS = [
        61, 146, 91, 181, 84, 17, 314, 405, 321, 375,  # Outer lips
        78, 191, 80, 81, 82, 13, 312, 311, 310, 415,   # Inner lips
        95, 88, 178, 87, 14, 317, 402, 318, 324, 308   # Additional
    ]

    def __init__(self):
        """Initialize the builder."""
        self.face_mesh = None
        self.use_mediapipe = False

        if HAS_MEDIAPIPE and MEDIAPIPE_LEGACY:
            try:
                self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.use_mediapipe = True
            except Exception as e:
                logger.warning(f"Could not initialize MediaPipe FaceMesh: {e}")
        elif HAS_MEDIAPIPE and not MEDIAPIPE_LEGACY:
            # New MediaPipe API - use OpenCV fallback for now
            logger.info("Using OpenCV face detection (MediaPipe tasks API not yet supported)")
            self.use_mediapipe = False

    def extract_mouth_from_frame(
        self,
        frame: np.ndarray,
        padding: float = 0.3
    ) -> Optional[MouthRegion]:
        """
        Extract mouth region from a frame.

        Args:
            frame: BGR image
            padding: Padding around mouth as fraction of mouth size

        Returns:
            MouthRegion or None if no face detected
        """
        if not self.use_mediapipe or self.face_mesh is None:
            return self._extract_mouth_opencv(frame, padding)

        # Convert to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]

        # Get mouth landmarks
        mouth_points = []
        for idx in self.MOUTH_LANDMARKS:
            lm = landmarks.landmark[idx]
            mouth_points.append((int(lm.x * w), int(lm.y * h)))

        # Compute bounding box
        xs = [p[0] for p in mouth_points]
        ys = [p[1] for p in mouth_points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Add padding
        mouth_w = x_max - x_min
        mouth_h = y_max - y_min
        pad_x = int(mouth_w * padding)
        pad_y = int(mouth_h * padding)

        x1 = max(0, x_min - pad_x)
        y1 = max(0, y_min - pad_y)
        x2 = min(w, x_max + pad_x)
        y2 = min(h, y_max + pad_y)

        # Crop mouth region
        mouth_img = frame[y1:y2, x1:x2].copy()

        return MouthRegion(
            image=mouth_img,
            bbox=(x1, y1, x2 - x1, y2 - y1),
            landmarks=mouth_points
        )

    def _extract_mouth_opencv(
        self,
        frame: np.ndarray,
        padding: float = 0.3
    ) -> Optional[MouthRegion]:
        """Fallback mouth extraction using OpenCV Haar cascades."""
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None

        # Take largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # Estimate mouth region (bottom third of face)
        mouth_y = y + int(h * 0.6)
        mouth_h = int(h * 0.35)
        mouth_x = x + int(w * 0.2)
        mouth_w = int(w * 0.6)

        # Add padding
        pad_x = int(mouth_w * padding)
        pad_y = int(mouth_h * padding)

        x1 = max(0, mouth_x - pad_x)
        y1 = max(0, mouth_y - pad_y)
        x2 = min(frame.shape[1], mouth_x + mouth_w + pad_x)
        y2 = min(frame.shape[0], mouth_y + mouth_h + pad_y)

        mouth_img = frame[y1:y2, x1:x2].copy()

        return MouthRegion(
            image=mouth_img,
            bbox=(x1, y1, x2 - x1, y2 - y1)
        )

    def build_from_video(
        self,
        video_path: str,
        subject_id: str,
        output_path: Optional[str] = None,
        sample_interval: int = 3,  # Sample every N frames
        auto_classify: bool = True
    ) -> VisemeLibrary:
        """
        Build viseme library from video.

        Args:
            video_path: Path to video file
            subject_id: Unique identifier for subject
            output_path: Where to save library (default: data/visemes/{subject_id})
            sample_interval: Sample every N frames
            auto_classify: Auto-classify visemes based on mouth shape

        Returns:
            VisemeLibrary ready for use
        """
        logger.info(f"Building viseme library from {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        library = VisemeLibrary(subject_id, output_path)
        frame_idx = 0
        extracted = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_interval == 0:
                mouth = self.extract_mouth_from_frame(frame)

                if mouth is not None:
                    mouth.frame_index = frame_idx

                    if auto_classify:
                        # Auto-classify based on mouth openness/shape
                        viseme_id = self._classify_mouth_shape(mouth)
                    else:
                        # Default to neutral, user can reclassify later
                        viseme_id = 0

                    library.add_viseme(viseme_id, mouth.image)
                    extracted += 1

                    # Store first frame as neutral reference
                    if library.neutral_frame is None:
                        library.neutral_frame = frame.copy()
                        library.face_bbox = self._get_face_bbox(frame)

            frame_idx += 1

        cap.release()

        logger.info(f"Extracted {extracted} mouth regions from {frame_idx} frames")

        # Save library
        library.save()

        return library

    def _classify_mouth_shape(self, mouth: MouthRegion) -> int:
        """
        Auto-classify mouth shape into viseme category.

        Uses simple heuristics based on mouth openness and width.
        """
        if mouth.landmarks is None:
            # Use image-based classification
            return self._classify_from_image(mouth.image)

        # Use landmarks for classification
        # Get vertical and horizontal mouth measurements
        # Top lip to bottom lip distance
        top_lip = mouth.landmarks[13]  # Upper lip center
        bottom_lip = mouth.landmarks[14]  # Lower lip center
        vertical_open = abs(bottom_lip[1] - top_lip[1])

        # Left to right corner distance
        left_corner = mouth.landmarks[0]  # Left corner
        right_corner = mouth.landmarks[10]  # Right corner
        horizontal_width = abs(right_corner[0] - left_corner[0])

        # Compute ratios
        if horizontal_width == 0:
            return 0

        openness_ratio = vertical_open / horizontal_width

        # Classify based on ratios
        if openness_ratio < 0.1:
            # Closed mouth
            if horizontal_width > 50:  # Wide/smile
                return 6  # Spread lips (smile)
            else:
                return 21  # Bilabial (closed)

        elif openness_ratio < 0.3:
            # Slightly open
            return 4  # Mid vowel

        elif openness_ratio < 0.5:
            # Moderately open
            return 1  # Open mid vowel

        else:
            # Wide open
            return 2  # Open wide vowel

    def _classify_from_image(self, mouth_img: np.ndarray) -> int:
        """Classify mouth shape from image (no landmarks)."""
        # Simple approach: measure dark region (mouth opening)
        gray = cv2.cvtColor(mouth_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)

        # Count dark pixels (mouth opening)
        dark_ratio = np.sum(thresh > 0) / thresh.size

        if dark_ratio < 0.1:
            return 21  # Closed (bilabial)
        elif dark_ratio < 0.2:
            return 4   # Slightly open
        elif dark_ratio < 0.35:
            return 1   # Mid open
        else:
            return 2   # Wide open

    def _get_face_bbox(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Get face bounding box from frame."""
        if self.use_mediapipe and self.face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb)

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]

                xs = [int(lm.x * w) for lm in landmarks.landmark]
                ys = [int(lm.y * h) for lm in landmarks.landmark]

                return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

        # Fallback to Haar cascade
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0:
            return tuple(max(faces, key=lambda f: f[2] * f[3]))

        return None

    def build_from_phrases(
        self,
        subject_id: str,
        capture_callback,
        output_path: Optional[str] = None
    ) -> VisemeLibrary:
        """
        Build library by prompting user to speak specific phrases.

        Each phrase is designed to capture specific visemes.

        Args:
            subject_id: Unique identifier
            capture_callback: Function that captures video while user speaks
                             signature: capture_callback(phrase: str) -> video_path
            output_path: Where to save library

        Returns:
            VisemeLibrary
        """
        # Phrases designed to capture all visemes
        phrases = [
            ("Pat bought my map", [21]),           # p, b, m (bilabials)
            ("Do not need it", [19]),              # d, t, n (alveolars)
            ("Get a cookie", [20]),                # k, g (velars)
            ("Fish and vineyard", [18]),           # f, v (labiodentals)
            ("See the zebra", [15]),               # s, z (sibilants)
            ("She chose the treasure", [16]),     # sh, ch, j (postalveolars)
            ("Think that thing", [17]),            # th (dentals)
            ("Hello, how are you", [12, 1]),       # h, open vowels
            ("We would want water", [7]),          # w, u (rounded)
            ("Easy street evening", [6]),          # ee, y (spread)
            ("Red light, rolling", [13, 14]),      # r, l
            ("Boy enjoys the toy", [10]),          # oi diphthong
            ("How now brown cow", [9]),            # ow diphthong
            ("My eyes find the sky", [11]),        # ai diphthong
            ("Go slow, hello", [8]),               # o, oh
        ]

        library = VisemeLibrary(subject_id, output_path)

        for phrase, target_visemes in phrases:
            print(f"\nPlease say: '{phrase}'")
            print(f"(Targets visemes: {target_visemes})")

            video_path = capture_callback(phrase)

            if video_path and os.path.exists(video_path):
                # Extract mouths from this video
                cap = cv2.VideoCapture(video_path)
                frame_idx = 0

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_idx % 2 == 0:  # Sample frequently
                        mouth = self.extract_mouth_from_frame(frame)
                        if mouth:
                            # Assign to target visemes round-robin
                            viseme_id = target_visemes[frame_idx % len(target_visemes)]
                            library.add_viseme(viseme_id, mouth.image)

                            if library.neutral_frame is None:
                                library.neutral_frame = frame.copy()
                                library.face_bbox = self._get_face_bbox(frame)

                    frame_idx += 1

                cap.release()

        library.save()
        return library


def demo():
    """Demo the viseme library builder."""
    # Create a test with webcam or video file
    import sys

    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        print("Usage: python viseme_library.py <video_path>")
        print("Or run with webcam test...")

        # Quick webcam test
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("No webcam available")
            return

        builder = VisemeLibraryBuilder()

        print("Press 'q' to quit, 's' to save a mouth snapshot")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            mouth = builder.extract_mouth_from_frame(frame)

            if mouth is not None:
                # Draw mouth region on frame
                x, y, w, h = mouth.bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Show mouth crop
                cv2.imshow("Mouth", cv2.resize(mouth.image, (200, 100)))

            cv2.imshow("Frame", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and mouth is not None:
                cv2.imwrite("/tmp/mouth_snapshot.png", mouth.image)
                print("Saved mouth snapshot")

        cap.release()
        cv2.destroyAllWindows()
        return

    # Build from video file
    builder = VisemeLibraryBuilder()
    library = builder.build_from_video(
        video_path,
        subject_id="test_subject",
        sample_interval=5
    )

    print(f"\nBuilt library with {len(library.templates)} viseme categories:")
    for vid, template in library.templates.items():
        print(f"  Viseme {vid}: {len(template.images)} variants - {template.description}")


if __name__ == "__main__":
    demo()
