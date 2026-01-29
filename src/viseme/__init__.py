"""Viseme-based lip sync module for real-time speech animation."""

# Core mapper is always available
from .phoneme_mapper import PhonemeToVisemeMapper, VISEME_DESCRIPTIONS, VisemeFrame

__all__ = [
    "PhonemeToVisemeMapper",
    "VISEME_DESCRIPTIONS",
    "VisemeFrame",
]

# Optional imports that require additional dependencies
def __getattr__(name):
    """Lazy import for optional components."""
    if name == "TTSWithVisemes":
        from .tts_viseme import TTSWithVisemes
        return TTSWithVisemes
    elif name == "VisemeEvent":
        from .tts_viseme import VisemeEvent
        return VisemeEvent
    elif name == "TTSResult":
        from .tts_viseme import TTSResult
        return TTSResult
    elif name == "VisemeLibraryBuilder":
        from .viseme_library import VisemeLibraryBuilder
        return VisemeLibraryBuilder
    elif name == "VisemeLibrary":
        from .viseme_library import VisemeLibrary
        return VisemeLibrary
    elif name == "RealtimeVisemeCompositor":
        from .realtime_compositor import RealtimeVisemeCompositor
        return RealtimeVisemeCompositor
    elif name == "StreamingVisemeCompositor":
        from .realtime_compositor import StreamingVisemeCompositor
        return StreamingVisemeCompositor
    raise AttributeError(f"module 'viseme' has no attribute '{name}'")
