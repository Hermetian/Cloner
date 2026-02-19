"""
PersonDescriptor - Extract and render text descriptions of a person for Sora prompts.

Sora's face detection restrictions prevent sending actual face photos.
This module captures a text description of the person from their face captures
(via Gemini Vision), then uses that description in Sora prompts to recreate
the person without sending their actual face.

Also provides background validation to ensure room/door captures are empty.

Usage:
    from src.video.person_descriptor import (
        PersonDescriptor,
        validate_empty_room,
        extract_person_descriptor,
        build_video_prompt,
    )

    # Validate empty room before capture
    is_empty, reason = validate_empty_room("room.png", api_key)

    # Extract description from face captures
    descriptor = extract_person_descriptor(["face1.png", "face2.png"], api_key)
    descriptor.save("person_descriptor.json")

    # Build Sora prompt with person description
    prompt = build_video_prompt("entry", descriptor)
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class PersonDescriptor:
    """Structured description of a person's appearance for video prompts.

    Attributes are organized in tiers:
    - Tier 1 (required): gender, age_range, skin_tone, hair_description
    - Tier 2 (important): face_shape, eye_description, build, facial_hair
    - Tier 3 (contextual): clothing_upper, clothing_lower, accessories
    """

    # Tier 1 - minimum viable description
    gender: str = ""
    age_range: str = ""
    skin_tone: str = ""
    hair_description: str = ""

    # Tier 2 - improves likeness
    face_shape: str = ""
    eye_description: str = ""
    build: str = ""
    facial_hair: str = ""

    # Tier 3 - contextual details
    clothing_upper: str = ""
    clothing_lower: str = ""
    accessories: str = ""

    def is_valid(self) -> bool:
        """Check that minimum Tier 1 fields are populated."""
        return all([self.gender, self.age_range, self.skin_tone, self.hair_description])

    def save(self, path: str) -> None:
        """Save descriptor to JSON file."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "PersonDescriptor":
        """Load descriptor from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _detect_face_local(image_path: str) -> bool:
    """Local face detection fallback using OpenCV Haar cascades.

    Returns True if a face is detected in the image.
    """
    try:
        import cv2
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        img = cv2.imread(image_path)
        if img is None:
            return False
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0
    except Exception as e:
        print(f"[DESCRIPTOR] Local face detection error: {e}")
        return False


def validate_empty_room(image_path: str, api_key: str) -> tuple[bool, str]:
    """Validate that a room/door capture contains no visible person.

    Uses Gemini Vision to check the image, with local Haar cascade fallback.

    Args:
        image_path: Path to the room/door capture image.
        api_key: Google API key for Gemini.

    Returns:
        (is_empty, reason): True if no person detected, with explanation.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        with open(image_path, "rb") as f:
            img_data = f.read()
        img_part = types.Part.from_bytes(data=img_data, mime_type="image/png")

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                "Look at this image of a room. Is any person, human figure, or body part visible? "
                "Reply with ONLY one word: EMPTY or PERSON_DETECTED",
                img_part,
            ],
        )

        result = response.candidates[0].content.parts[0].text.strip().upper()
        print(f"[DESCRIPTOR] Room validation: {result}")

        if "PERSON" in result:
            return False, "Person detected in frame — please step out and retake"
        return True, "Room is empty"

    except Exception as e:
        print(f"[DESCRIPTOR] Gemini validation failed ({e}), using local fallback")
        # Fallback to local face detection
        if _detect_face_local(image_path):
            return False, "Face detected in frame (local) — please step out and retake"
        return True, "Room appears empty (local check)"


def extract_person_descriptor(
    image_paths: list[str], api_key: str
) -> Optional[PersonDescriptor]:
    """Extract a structured person description from face capture images.

    Sends up to 5 best face captures to Gemini Vision and asks for a
    structured JSON description matching the PersonDescriptor schema.

    Args:
        image_paths: List of face capture image paths.
        api_key: Google API key for Gemini.

    Returns:
        PersonDescriptor if extraction succeeds, None on failure.
    """
    if not image_paths:
        print("[DESCRIPTOR] No face images provided")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Use up to 5 images
        selected = image_paths[:5]

        content = [
            "Analyze these photos of a person and provide a detailed physical description "
            "as a JSON object with these exact keys:\n"
            "- gender: male/female\n"
            "- age_range: e.g. 'late 20s', 'early 40s'\n"
            "- skin_tone: e.g. 'fair', 'light', 'medium', 'olive', 'dark'\n"
            "- hair_description: color, length, style, e.g. 'short straight dark brown hair parted to the side'\n"
            "- face_shape: e.g. 'oval', 'round', 'square', 'angular'\n"
            "- eye_description: color and any notable features\n"
            "- build: e.g. 'slim', 'medium', 'athletic', 'stocky'\n"
            "- facial_hair: e.g. 'clean-shaven', 'light stubble', 'full beard'\n"
            "- clothing_upper: what they're wearing on top, e.g. 'olive green t-shirt'\n"
            "- clothing_lower: pants/shorts if visible\n"
            "- accessories: glasses, watch, jewelry, etc.\n\n"
            "Return ONLY the JSON object, no markdown fences or extra text."
        ]

        for i, path in enumerate(selected):
            with open(path, "rb") as f:
                img_data = f.read()
            content.append(f"Photo {i + 1}:")
            content.append(types.Part.from_bytes(data=img_data, mime_type="image/png"))

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=content,
        )

        raw = response.candidates[0].content.parts[0].text.strip()
        print(f"[DESCRIPTOR] Gemini raw response: {raw[:200]}")

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw = "\n".join(lines)

        data = json.loads(raw)

        descriptor = PersonDescriptor(
            gender=data.get("gender", ""),
            age_range=data.get("age_range", ""),
            skin_tone=data.get("skin_tone", ""),
            hair_description=data.get("hair_description", ""),
            face_shape=data.get("face_shape", ""),
            eye_description=data.get("eye_description", ""),
            build=data.get("build", ""),
            facial_hair=data.get("facial_hair", ""),
            clothing_upper=data.get("clothing_upper", ""),
            clothing_lower=data.get("clothing_lower", ""),
            accessories=data.get("accessories", ""),
        )

        print(f"[DESCRIPTOR] Extracted: {descriptor.gender}, {descriptor.age_range}, "
              f"hair={descriptor.hair_description}, valid={descriptor.is_valid()}")
        return descriptor

    except json.JSONDecodeError as e:
        print(f"[DESCRIPTOR] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[DESCRIPTOR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def render_person_prompt(descriptor: PersonDescriptor, context: str = "full") -> str:
    """Convert a PersonDescriptor into natural language for Sora prompts.

    Args:
        descriptor: The person description.
        context: One of "full" (entry/exit), "seated" (idle), "brief" (short ref).

    Returns:
        Natural language description string.
    """
    parts = []

    # Tier 1 - always included, front-loaded
    age_gender = f"A {descriptor.age_range} {descriptor.gender}" if descriptor.age_range else f"A {descriptor.gender}"
    if descriptor.skin_tone:
        age_gender += f" with {descriptor.skin_tone} skin"
    parts.append(age_gender)

    if descriptor.hair_description:
        parts.append(descriptor.hair_description)

    if descriptor.face_shape:
        parts.append(f"{descriptor.face_shape} face")

    # Tier 2 - include for full/seated
    if context in ("full", "seated"):
        if descriptor.facial_hair:
            parts.append(descriptor.facial_hair)
        if descriptor.build and context == "full":
            parts.append(f"{descriptor.build} build")

    # Tier 3 - clothing
    clothing = []
    if descriptor.clothing_upper:
        clothing.append(f"wearing {descriptor.clothing_upper}")
    if descriptor.clothing_lower and context == "full":
        clothing.append(descriptor.clothing_lower)
    if clothing:
        parts.append(", ".join(clothing))

    if descriptor.accessories and context != "brief":
        parts.append(descriptor.accessories)

    # Join with commas, end with period
    result = ", ".join(parts) + "."

    # Clean up double spaces or repeated commas
    result = result.replace("  ", " ").replace(", ,", ",")
    return result


def build_video_prompt(video_type: str, descriptor: PersonDescriptor) -> str:
    """Build a complete Sora video prompt combining person description with scene action.

    Args:
        video_type: One of "entry", "idle", "exit".
        descriptor: The person description to include.

    Returns:
        Complete prompt string for Sora.
    """
    if video_type == "entry":
        person = render_person_prompt(descriptor, "full")
        return (
            f"{person} The door opens. This person enters through the door, "
            "walks across the room, and sits down in the chair on the left. "
            "The door closes. Smooth natural movement."
        )

    elif video_type == "idle":
        person = render_person_prompt(descriptor, "seated")
        return (
            f"{person} Seated in a chair, breathing naturally. "
            "Subtle mouth movement as if about to speak. Blinks occasionally. "
            "Very subtle idle motion for seamless loop."
        )

    elif video_type == "exit":
        person = render_person_prompt(descriptor, "full")
        return (
            f"{person} This person stands up from the chair, walks around behind the large chair, "
            "approaches the door, opens it and exits. The door closes leaving the room empty. "
            "Smooth natural walking."
        )

    else:
        raise ValueError(f"Unknown video type: {video_type}")
