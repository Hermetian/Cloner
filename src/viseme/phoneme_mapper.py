"""
Phoneme to Viseme mapping for lip sync.

Based on the standard 22 viseme set used by Azure Speech and other TTS systems.
Maps English phonemes (IPA) to visual mouth shapes.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import re

# Standard 22 viseme set with IPA phonemes and descriptions
VISEME_MAP = {
    # Viseme 0: Silence/neutral
    0: {"phonemes": [], "description": "Silence/neutral", "mouth": "closed"},

    # Viseme 1: æ, ə, ʌ (as in "bat", "about", "but")
    1: {"phonemes": ["æ", "ə", "ʌ", "a"], "description": "Open mid vowel", "mouth": "open_mid"},

    # Viseme 2: ɑ (as in "father")
    2: {"phonemes": ["ɑ", "ɑː"], "description": "Open back vowel", "mouth": "open_wide"},

    # Viseme 3: ɔ (as in "thought")
    3: {"phonemes": ["ɔ", "ɔː"], "description": "Open-mid back rounded", "mouth": "open_round"},

    # Viseme 4: ɛ, ʊ (as in "bed", "foot")
    4: {"phonemes": ["ɛ", "ʊ", "e"], "description": "Mid vowels", "mouth": "slight_open"},

    # Viseme 5: ɝ (as in "bird")
    5: {"phonemes": ["ɝ", "ɜː", "ər"], "description": "R-colored vowel", "mouth": "slight_round"},

    # Viseme 6: j, i, ɪ (as in "yes", "beat", "bit")
    6: {"phonemes": ["j", "i", "iː", "ɪ"], "description": "High front vowel", "mouth": "smile"},

    # Viseme 7: w, u, uː (as in "we", "boot")
    7: {"phonemes": ["w", "u", "uː"], "description": "High back rounded", "mouth": "pucker"},

    # Viseme 8: o, oʊ (as in "go")
    8: {"phonemes": ["o", "oʊ", "əʊ"], "description": "Mid back rounded", "mouth": "round"},

    # Viseme 9: aʊ (as in "cow")
    9: {"phonemes": ["aʊ"], "description": "Open to round diphthong", "mouth": "open_to_round"},

    # Viseme 10: ɔɪ (as in "boy")
    10: {"phonemes": ["ɔɪ"], "description": "Round to spread diphthong", "mouth": "round_to_spread"},

    # Viseme 11: aɪ (as in "buy")
    11: {"phonemes": ["aɪ"], "description": "Open to spread diphthong", "mouth": "open_to_spread"},

    # Viseme 12: h (as in "hello")
    12: {"phonemes": ["h"], "description": "Glottal fricative", "mouth": "open_relaxed"},

    # Viseme 13: ɹ (as in "red")
    13: {"phonemes": ["ɹ", "r"], "description": "Alveolar approximant", "mouth": "slight_pucker"},

    # Viseme 14: l (as in "light")
    14: {"phonemes": ["l"], "description": "Lateral approximant", "mouth": "tongue_up"},

    # Viseme 15: s, z (as in "see", "zoo")
    15: {"phonemes": ["s", "z"], "description": "Alveolar sibilants", "mouth": "teeth_together"},

    # Viseme 16: ʃ, tʃ, dʒ, ʒ (as in "she", "church", "judge", "measure")
    16: {"phonemes": ["ʃ", "tʃ", "dʒ", "ʒ", "ch", "sh"], "description": "Postalveolar", "mouth": "pucker_slight"},

    # Viseme 17: θ, ð (as in "think", "this")
    17: {"phonemes": ["θ", "ð", "th"], "description": "Dental fricatives", "mouth": "tongue_teeth"},

    # Viseme 18: f, v (as in "fish", "very")
    18: {"phonemes": ["f", "v"], "description": "Labiodental fricatives", "mouth": "teeth_lip"},

    # Viseme 19: d, t, n (as in "dog", "top", "no")
    19: {"phonemes": ["d", "t", "n"], "description": "Alveolar stops/nasal", "mouth": "tongue_alveolar"},

    # Viseme 20: k, g, ŋ (as in "cat", "go", "sing")
    20: {"phonemes": ["k", "g", "ŋ", "ng"], "description": "Velar consonants", "mouth": "back_tongue"},

    # Viseme 21: p, b, m (as in "pat", "bat", "mat")
    21: {"phonemes": ["p", "b", "m"], "description": "Bilabial consonants", "mouth": "lips_together"},
}

# Simplified letter-to-viseme mapping for quick lookup (English approximation)
LETTER_TO_VISEME = {
    # Vowels (context-dependent, using common pronunciations)
    'a': 1,   # "a" as in "cat" → æ
    'e': 4,   # "e" as in "bed" → ɛ
    'i': 6,   # "i" as in "bit" → ɪ
    'o': 8,   # "o" as in "go" → oʊ
    'u': 7,   # "u" as in "put" → ʊ

    # Consonants
    'b': 21, 'p': 21, 'm': 21,  # Bilabials
    'd': 19, 't': 19, 'n': 19,  # Alveolars
    'k': 20, 'g': 20,           # Velars
    'f': 18, 'v': 18,           # Labiodentals
    's': 15, 'z': 15,           # Sibilants
    'l': 14,                     # Lateral
    'r': 13,                     # Rhotic
    'h': 12,                     # Glottal
    'w': 7,                      # Labial-velar
    'y': 6,                      # Palatal
    'j': 6,                      # Same as 'y'

    # Digraph hints (will be handled specially)
    'c': 15,  # Default to 's' sound, context-dependent
    'q': 20,  # Usually 'kw'
    'x': 15,  # Usually 'ks'

    # Space/punctuation
    ' ': 0,
    '.': 0,
    ',': 0,
    '!': 0,
    '?': 0,
    '-': 0,
}

# Common English digraphs to viseme
DIGRAPH_TO_VISEME = {
    'th': 17,  # θ or ð
    'sh': 16,  # ʃ
    'ch': 16,  # tʃ
    'ng': 20,  # ŋ
    'wh': 7,   # w (in most dialects)
    'ph': 18,  # f
    'ck': 20,  # k
    'gh': 0,   # Usually silent
    'oo': 7,   # uː
    'ee': 6,   # iː
    'ea': 6,   # iː (as in "eat")
    'ai': 11,  # aɪ (as in "rain")
    'ay': 11,  # aɪ
    'oi': 10,  # ɔɪ
    'oy': 10,  # ɔɪ
    'ou': 9,   # aʊ
    'ow': 9,   # aʊ (as in "cow")
    'ew': 7,   # uː
}

# Descriptions for UI/debugging
VISEME_DESCRIPTIONS = {
    viseme_id: info["description"]
    for viseme_id, info in VISEME_MAP.items()
}


@dataclass
class VisemeFrame:
    """A single viseme with timing information."""
    viseme_id: int
    start_time: float  # seconds
    duration: float    # seconds
    intensity: float = 1.0  # 0.0 to 1.0 for blending

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration


class PhonemeToVisemeMapper:
    """
    Maps text/phonemes to viseme sequences.

    Supports both direct character mapping (fast, approximate) and
    IPA phoneme mapping (accurate, requires phonemizer).
    """

    def __init__(self, use_phonemizer: bool = False):
        """
        Initialize the mapper.

        Args:
            use_phonemizer: If True, use g2p library for accurate phoneme conversion.
                           If False, use fast character-based approximation.
        """
        self.use_phonemizer = use_phonemizer
        self._phonemizer = None

        if use_phonemizer:
            try:
                from g2p_en import G2p
                self._phonemizer = G2p()
            except ImportError:
                print("Warning: g2p_en not installed. Using character-based mapping.")
                self.use_phonemizer = False

    def text_to_visemes(
        self,
        text: str,
        duration: float,
        min_viseme_duration: float = 0.05,  # 50ms minimum
        coarticulation: bool = True
    ) -> List[VisemeFrame]:
        """
        Convert text to a sequence of viseme frames.

        Args:
            text: Input text to convert
            duration: Total duration in seconds for the viseme sequence
            min_viseme_duration: Minimum duration per viseme (for natural pacing)
            coarticulation: Apply smoothing between adjacent visemes

        Returns:
            List of VisemeFrame objects with timing
        """
        # Get raw viseme sequence
        viseme_ids = self._text_to_viseme_ids(text)

        if not viseme_ids:
            return [VisemeFrame(0, 0.0, duration)]

        # Calculate timing
        frames = self._assign_timing(viseme_ids, duration, min_viseme_duration)

        # Apply coarticulation (smoothing)
        if coarticulation:
            frames = self._apply_coarticulation(frames)

        return frames

    def _text_to_viseme_ids(self, text: str) -> List[int]:
        """Convert text to raw viseme ID sequence."""
        text = text.lower().strip()

        if self.use_phonemizer and self._phonemizer:
            return self._phonemes_to_visemes(self._phonemizer(text))
        else:
            return self._characters_to_visemes(text)

    def _characters_to_visemes(self, text: str) -> List[int]:
        """Fast character-based viseme mapping."""
        visemes = []
        i = 0

        while i < len(text):
            # Check for digraphs first (2 characters)
            if i + 1 < len(text):
                digraph = text[i:i+2]
                if digraph in DIGRAPH_TO_VISEME:
                    visemes.append(DIGRAPH_TO_VISEME[digraph])
                    i += 2
                    continue

            # Single character
            char = text[i]
            if char in LETTER_TO_VISEME:
                visemes.append(LETTER_TO_VISEME[char])
            else:
                # Unknown character, use silence
                visemes.append(0)
            i += 1

        # Remove consecutive duplicates (coarticulation prep)
        if visemes:
            deduped = [visemes[0]]
            for v in visemes[1:]:
                if v != deduped[-1] or v == 0:  # Keep silences separate
                    deduped.append(v)
            visemes = deduped

        return visemes

    def _phonemes_to_visemes(self, phonemes: List[str]) -> List[int]:
        """Convert IPA phonemes to visemes."""
        visemes = []

        for phoneme in phonemes:
            phoneme = phoneme.lower().strip()
            if not phoneme:
                continue

            # Search for matching viseme
            found = False
            for viseme_id, info in VISEME_MAP.items():
                if phoneme in info["phonemes"]:
                    visemes.append(viseme_id)
                    found = True
                    break

            if not found:
                # Try partial match
                for viseme_id, info in VISEME_MAP.items():
                    for p in info["phonemes"]:
                        if phoneme.startswith(p) or p.startswith(phoneme):
                            visemes.append(viseme_id)
                            found = True
                            break
                    if found:
                        break

            if not found:
                # Default to neutral
                visemes.append(0)

        return visemes

    def _assign_timing(
        self,
        viseme_ids: List[int],
        total_duration: float,
        min_duration: float
    ) -> List[VisemeFrame]:
        """Assign timing to viseme sequence."""
        n = len(viseme_ids)

        # Base duration per viseme
        base_duration = total_duration / n

        # Adjust to meet minimum duration
        if base_duration < min_duration:
            base_duration = min_duration

        frames = []
        current_time = 0.0

        for i, viseme_id in enumerate(viseme_ids):
            # Vary duration slightly for naturalness
            # Consonants are typically shorter than vowels
            if viseme_id in [15, 16, 17, 18, 19, 20, 21]:  # Consonants
                duration = base_duration * 0.7
            elif viseme_id == 0:  # Silence
                duration = base_duration * 0.5
            else:  # Vowels
                duration = base_duration * 1.2

            # Don't exceed total duration
            if current_time + duration > total_duration:
                duration = total_duration - current_time

            if duration > 0:
                frames.append(VisemeFrame(
                    viseme_id=viseme_id,
                    start_time=current_time,
                    duration=duration
                ))
                current_time += duration

        return frames

    def _apply_coarticulation(self, frames: List[VisemeFrame]) -> List[VisemeFrame]:
        """Apply coarticulation smoothing between visemes."""
        if len(frames) < 2:
            return frames

        # Add transition intensity based on viseme distance
        smoothed = []

        for i, frame in enumerate(frames):
            # Intensity ramps up/down at boundaries
            if i == 0:
                frame.intensity = 0.8  # Slightly reduced start
            elif i == len(frames) - 1:
                frame.intensity = 0.8  # Slightly reduced end
            else:
                # Check if transitioning between very different mouth shapes
                prev_id = frames[i-1].viseme_id
                curr_id = frame.viseme_id

                # Similar mouth shapes blend more smoothly
                if self._viseme_similarity(prev_id, curr_id) > 0.7:
                    frame.intensity = 1.0
                else:
                    frame.intensity = 0.9

            smoothed.append(frame)

        return smoothed

    def _viseme_similarity(self, v1: int, v2: int) -> float:
        """Compute similarity between two visemes (0.0 to 1.0)."""
        if v1 == v2:
            return 1.0

        # Group similar visemes
        groups = [
            {0},           # Silence
            {1, 2, 3, 4},  # Open vowels
            {6, 11},       # Spread/smile
            {7, 8},        # Rounded
            {9, 10},       # Diphthongs with round
            {15, 16},      # Sibilants
            {18, 21},      # Lip consonants
            {19, 20},      # Tongue consonants
        ]

        for group in groups:
            if v1 in group and v2 in group:
                return 0.8

        return 0.3


def demo():
    """Demo the phoneme mapper."""
    mapper = PhonemeToVisemeMapper(use_phonemizer=False)

    text = "Hello, how are you today?"
    duration = 2.5  # seconds

    frames = mapper.text_to_visemes(text, duration)

    print(f"Text: {text}")
    print(f"Duration: {duration}s")
    print(f"Generated {len(frames)} viseme frames:\n")

    for frame in frames:
        desc = VISEME_DESCRIPTIONS.get(frame.viseme_id, "Unknown")
        print(f"  {frame.start_time:.3f}s - {frame.end_time:.3f}s: "
              f"Viseme {frame.viseme_id:2d} ({desc}) @ {frame.intensity:.1f}")


if __name__ == "__main__":
    demo()
