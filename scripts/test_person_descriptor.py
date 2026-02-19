#!/usr/bin/env python3
"""
Smoke test for PersonDescriptor extraction and prompt rendering.

Usage:
    python scripts/test_person_descriptor.py <face_image_path> [face_image_2] ...

    # With a room image for empty-room validation:
    python scripts/test_person_descriptor.py --room room.png <face_image_path>

Requires GOOGLE_API_KEY in environment or .env file.
"""

import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


def main():
    parser = argparse.ArgumentParser(description="Test PersonDescriptor extraction")
    parser.add_argument("face_images", nargs="+", help="Path(s) to face capture images")
    parser.add_argument("--room", help="Path to room image for empty-room validation")
    args = parser.parse_args()

    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    from src.video.person_descriptor import (
        PersonDescriptor,
        validate_empty_room,
        extract_person_descriptor,
        render_person_prompt,
        build_video_prompt,
    )

    # --- Room validation test ---
    if args.room:
        print(f"\n{'='*60}")
        print(f"ROOM VALIDATION: {args.room}")
        print(f"{'='*60}")
        is_empty, reason = validate_empty_room(args.room, GOOGLE_API_KEY)
        print(f"  Empty: {is_empty}")
        print(f"  Reason: {reason}")

    # --- Person descriptor extraction ---
    print(f"\n{'='*60}")
    print(f"PERSON DESCRIPTOR EXTRACTION")
    print(f"  Images: {args.face_images}")
    print(f"{'='*60}")

    # Verify files exist
    for path in args.face_images:
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            sys.exit(1)

    descriptor = extract_person_descriptor(args.face_images, GOOGLE_API_KEY)

    if descriptor is None:
        print("\nFAILED: Extraction returned None")
        sys.exit(1)

    print(f"\n  Valid: {descriptor.is_valid()}")
    print(f"  Gender: {descriptor.gender}")
    print(f"  Age: {descriptor.age_range}")
    print(f"  Skin: {descriptor.skin_tone}")
    print(f"  Hair: {descriptor.hair_description}")
    print(f"  Face: {descriptor.face_shape}")
    print(f"  Eyes: {descriptor.eye_description}")
    print(f"  Build: {descriptor.build}")
    print(f"  Facial hair: {descriptor.facial_hair}")
    print(f"  Clothing upper: {descriptor.clothing_upper}")
    print(f"  Clothing lower: {descriptor.clothing_lower}")
    print(f"  Accessories: {descriptor.accessories}")

    # --- Save/load test ---
    test_path = "/tmp/test_person_descriptor.json"
    descriptor.save(test_path)
    loaded = PersonDescriptor.load(test_path)
    assert loaded.gender == descriptor.gender, "Save/load mismatch!"
    assert loaded.hair_description == descriptor.hair_description, "Save/load mismatch!"
    print(f"\n  Save/load: OK ({test_path})")
    os.unlink(test_path)

    # --- Prompt rendering ---
    print(f"\n{'='*60}")
    print(f"PROMPT RENDERING")
    print(f"{'='*60}")

    for ctx in ("full", "seated", "brief"):
        rendered = render_person_prompt(descriptor, ctx)
        print(f"\n  [{ctx}]: {rendered}")

    # --- Video prompts ---
    print(f"\n{'='*60}")
    print(f"VIDEO PROMPTS")
    print(f"{'='*60}")

    for vtype in ("entry", "idle", "exit"):
        prompt = build_video_prompt(vtype, descriptor)
        print(f"\n  [{vtype}]: {prompt}")

    print(f"\n{'='*60}")
    print("ALL TESTS PASSED")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
