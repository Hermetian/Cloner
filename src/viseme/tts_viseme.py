"""
TTS with viseme timing output.

Integrates with ElevenLabs timestamps API to generate speech
with synchronized viseme data for lip animation.
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests

from .phoneme_mapper import PhonemeToVisemeMapper, VisemeFrame

logger = logging.getLogger(__name__)


@dataclass
class VisemeEvent:
    """A viseme event with audio timing."""
    viseme_id: int
    start_time_ms: int
    end_time_ms: int
    character: str
    intensity: float = 1.0

    def to_dict(self):
        return asdict(self)


@dataclass
class TTSResult:
    """Result from TTS generation with viseme data."""
    audio_path: str
    audio_duration_ms: int
    viseme_events: List[VisemeEvent]
    text: str

    def to_json(self, path: str):
        """Save viseme data to JSON file."""
        data = {
            "audio_path": self.audio_path,
            "audio_duration_ms": self.audio_duration_ms,
            "text": self.text,
            "viseme_events": [e.to_dict() for e in self.viseme_events]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "TTSResult":
        """Load viseme data from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            audio_path=data["audio_path"],
            audio_duration_ms=data["audio_duration_ms"],
            text=data["text"],
            viseme_events=[VisemeEvent(**e) for e in data["viseme_events"]]
        )


class TTSWithVisemes:
    """
    Text-to-speech with viseme timing output.

    Uses ElevenLabs timestamps API to get character-level timing,
    then converts to viseme sequences for lip animation.
    """

    ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_phonemizer: bool = False
    ):
        """
        Initialize TTS with viseme output.

        Args:
            api_key: ElevenLabs API key (or set ELEVENLABS_API_KEY env var)
            use_phonemizer: Use accurate phoneme conversion (requires g2p_en)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key required")

        self.mapper = PhonemeToVisemeMapper(use_phonemizer=use_phonemizer)

    def generate_with_visemes(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> TTSResult:
        """
        Generate speech with synchronized viseme data.

        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            output_path: Path to save audio file
            model_id: ElevenLabs model to use
            stability: Voice stability (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)

        Returns:
            TTSResult with audio path and viseme events
        """
        logger.info(f"Generating TTS with visemes for {len(text)} characters")

        # Call ElevenLabs with timestamps
        url = f"{self.ELEVENLABS_API_BASE}/text-to-speech/{voice_id}/with-timestamps"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        # Decode and save audio
        audio_bytes = base64.b64decode(data["audio_base64"])
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(audio_bytes)

        # Extract timing data
        alignment = data.get("alignment", {})
        characters = alignment.get("characters", [])
        start_times = alignment.get("character_start_times_seconds", [])
        end_times = alignment.get("character_end_times_seconds", [])

        # Convert to viseme events
        viseme_events = self._timestamps_to_visemes(
            characters, start_times, end_times
        )

        # Calculate total duration
        if end_times:
            duration_ms = int(max(end_times) * 1000)
        else:
            duration_ms = 0

        logger.info(f"Generated {len(viseme_events)} viseme events, duration: {duration_ms}ms")

        return TTSResult(
            audio_path=str(output_path),
            audio_duration_ms=duration_ms,
            viseme_events=viseme_events,
            text=text
        )

    def _timestamps_to_visemes(
        self,
        characters: List[str],
        start_times: List[float],
        end_times: List[float]
    ) -> List[VisemeEvent]:
        """Convert character timestamps to viseme events."""
        if not characters or not start_times or not end_times:
            return []

        events = []

        for char, start, end in zip(characters, start_times, end_times):
            # Get viseme for this character
            viseme_ids = self.mapper._characters_to_visemes(char.lower())
            viseme_id = viseme_ids[0] if viseme_ids else 0

            events.append(VisemeEvent(
                viseme_id=viseme_id,
                start_time_ms=int(start * 1000),
                end_time_ms=int(end * 1000),
                character=char
            ))

        # Merge consecutive identical visemes for smoother animation
        merged = self._merge_consecutive_visemes(events)

        return merged

    def _merge_consecutive_visemes(
        self,
        events: List[VisemeEvent],
        min_duration_ms: int = 50
    ) -> List[VisemeEvent]:
        """Merge consecutive identical visemes."""
        if not events:
            return []

        merged = [events[0]]

        for event in events[1:]:
            last = merged[-1]

            # Merge if same viseme and short duration
            if (event.viseme_id == last.viseme_id and
                event.start_time_ms - last.end_time_ms < 20):
                # Extend the last event
                last.end_time_ms = event.end_time_ms
                last.character += event.character
            else:
                merged.append(event)

        # Apply minimum duration
        for event in merged:
            duration = event.end_time_ms - event.start_time_ms
            if duration < min_duration_ms:
                event.end_time_ms = event.start_time_ms + min_duration_ms

        return merged

    def generate_visemes_only(
        self,
        text: str,
        duration_seconds: float
    ) -> List[VisemeEvent]:
        """
        Generate viseme sequence without calling TTS API.

        Useful for testing or when audio is generated separately.

        Args:
            text: Text to convert to visemes
            duration_seconds: Total duration for timing

        Returns:
            List of VisemeEvent objects
        """
        frames = self.mapper.text_to_visemes(text, duration_seconds)

        return [
            VisemeEvent(
                viseme_id=f.viseme_id,
                start_time_ms=int(f.start_time * 1000),
                end_time_ms=int(f.end_time * 1000),
                character="",
                intensity=f.intensity
            )
            for f in frames
        ]


def demo():
    """Demo TTS with visemes (requires API key)."""
    import sys

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("Set ELEVENLABS_API_KEY to run full demo")
        print("Running offline viseme generation demo instead...\n")

        tts = TTSWithVisemes.__new__(TTSWithVisemes)
        tts.mapper = PhonemeToVisemeMapper()

        events = tts.generate_visemes_only(
            "Hello, how are you today?",
            duration_seconds=2.5
        )

        print("Generated viseme events:")
        for event in events:
            print(f"  {event.start_time_ms:4d}ms - {event.end_time_ms:4d}ms: "
                  f"Viseme {event.viseme_id:2d}")
        return

    # Full demo with API
    tts = TTSWithVisemes()

    # You would need a valid voice_id here
    result = tts.generate_with_visemes(
        text="Hello, this is a test of the viseme system.",
        voice_id="YOUR_VOICE_ID",
        output_path="/tmp/test_viseme.mp3"
    )

    print(f"Audio saved to: {result.audio_path}")
    print(f"Duration: {result.audio_duration_ms}ms")
    print(f"Viseme events: {len(result.viseme_events)}")

    for event in result.viseme_events[:10]:
        print(f"  {event.start_time_ms:4d}ms: Viseme {event.viseme_id} '{event.character}'")


if __name__ == "__main__":
    demo()
