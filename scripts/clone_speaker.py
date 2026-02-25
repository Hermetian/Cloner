#!/usr/bin/env python3
"""
Clone Speaker - TTS interface for the Clone during idle loop

Runs alongside clone_controller.py when the clone is active (IdleLoop state).
Takes text input and speaks it through ElevenLabs TTS, routing audio to
a virtual audio device that can be mixed with your mic for Google Meet.

Usage:
    python clone_speaker.py                    # Interactive mode
    python clone_speaker.py --voice VOICE_ID   # Use specific voice
    python clone_speaker.py --list             # List available voices

Architecture:
    You (mic) ----------------------+
                                    +--> VoiceMeeter/VB-Cable --> Google Meet
    Clone (ElevenLabs TTS) ---------+

The clone speaks through a virtual audio device. Use VoiceMeeter or similar
to mix it with your real microphone for Meet.
"""

import os
import sys
import io
import threading
import queue
from pathlib import Path

# Load environment
from dotenv import load_dotenv
_master_env = Path.home() / "iCloudDrive" / "Documents" / "Projects" / "ClaudeCommander" / "master.env"
if _master_env.exists():
    load_dotenv(_master_env)
else:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1"

# Load voice_id from config
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
try:
    from src.utils.config_loader import ConfigLoader
    _config = ConfigLoader(str(_project_root / "config" / "config.yaml"))
    DEFAULT_VOICE_ID = _config.get("tts", "voice_id", default="nf18MnSL81anCHgQgL1A")
except Exception:
    DEFAULT_VOICE_ID = "nf18MnSL81anCHgQgL1A"


class CloneSpeaker:
    """Handles TTS generation and playback for the clone."""

    def __init__(self, voice_id: str = DEFAULT_VOICE_ID,
                 stability: float = 0.5, similarity_boost: float = 0.75):
        self.voice_id = voice_id
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.stop_event = threading.Event()

        # Validate API key
        if not ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not set. Check .env file.")

    def list_voices(self):
        """List all available ElevenLabs voices."""
        import requests

        url = f"{BASE_URL}/voices"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["voices"]
        else:
            raise Exception(f"Failed to list voices: {response.text}")

    def generate_speech_stream(self, text: str):
        """Generate speech using ElevenLabs streaming API.

        Returns audio as bytes (MP3 format).
        """
        import requests

        url = f"{BASE_URL}/text-to-speech/{self.voice_id}/stream"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost
            }
        }

        response = requests.post(url, headers=headers, json=data, stream=True)

        if response.status_code != 200:
            raise Exception(f"TTS failed: {response.text}")

        # Collect all chunks into a buffer
        audio_buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                audio_buffer.write(chunk)

        audio_buffer.seek(0)
        return audio_buffer.read()

    def play_audio(self, audio_bytes: bytes, output_device: str = None):
        """Play audio bytes through the specified output device."""
        try:
            from pydub import AudioSegment
            from pydub.playback import play

            audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            play(audio)

        except ImportError:
            import tempfile
            import subprocess
            import platform

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            if platform.system() == "Windows":
                subprocess.run(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{temp_path}').PlaySync()"],
                    check=False, capture_output=True
                )
            else:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_path],
                              check=False, capture_output=True)

            os.unlink(temp_path)

    def speak(self, text: str, blocking: bool = True):
        """Speak the given text."""
        if blocking:
            self._speak_now(text)
        else:
            self.speech_queue.put(text)

    def _speak_now(self, text: str):
        """Generate and play speech immediately."""
        self.is_speaking = True
        try:
            print(f"  [Clone speaking: \"{text[:50]}{'...' if len(text) > 50 else ''}\"]")
            audio = self.generate_speech_stream(text)
            self.play_audio(audio)
        finally:
            self.is_speaking = False

    def _speech_worker(self):
        """Background worker that processes the speech queue."""
        while not self.stop_event.is_set():
            try:
                text = self.speech_queue.get(timeout=0.5)
                self._speak_now(text)
                self.speech_queue.task_done()
            except queue.Empty:
                continue

    def start_async_mode(self):
        """Start background thread for non-blocking speech."""
        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        """Stop the async speech worker."""
        self.stop_event.set()


def interactive_mode(speaker: CloneSpeaker):
    """Interactive command-line mode for typing what the clone should say."""
    print("\n" + "="*60)
    print("CLONE SPEAKER - Interactive Mode")
    print("="*60)
    print(f"Voice: {speaker.voice_id}")
    print("\nType what the clone should say, press Enter to speak.")
    print("Commands:")
    print("  /quit    - Exit")
    print("  /voice   - List available voices")
    print("  /set ID  - Change voice to ID")
    print("="*60 + "\n")

    while True:
        try:
            text = input("Clone says> ").strip()

            if not text:
                continue

            if text == "/quit":
                print("Goodbye!")
                break

            if text == "/voice":
                print("\nAvailable voices:")
                for v in speaker.list_voices():
                    marker = " <-- current" if v['voice_id'] == speaker.voice_id else ""
                    print(f"  [{v['voice_id'][:12]}...] {v['name']}{marker}")
                print()
                continue

            if text.startswith("/set "):
                new_id = text[5:].strip()
                speaker.voice_id = new_id
                print(f"Voice changed to: {new_id}")
                continue

            # Speak the text
            speaker.speak(text)

        except KeyboardInterrupt:
            print("\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clone Speaker - TTS for the video clone")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID, help="ElevenLabs voice ID")
    parser.add_argument("--list", action="store_true", help="List available voices")
    parser.add_argument("--say", type=str, help="Speak this text and exit")
    parser.add_argument("--stability", type=float, default=0.5, help="Voice stability (0-1)")
    parser.add_argument("--similarity", type=float, default=0.75, help="Similarity boost (0-1)")

    args = parser.parse_args()

    try:
        speaker = CloneSpeaker(
            voice_id=args.voice,
            stability=args.stability,
            similarity_boost=args.similarity
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.list:
        print("\nAvailable voices:")
        print("-" * 60)
        for v in speaker.list_voices():
            category = v.get("category", "unknown")
            print(f"  [{v['voice_id']}] {v['name']} ({category})")
        print("-" * 60)
        return

    if args.say:
        speaker.speak(args.say)
        return

    # Interactive mode
    interactive_mode(speaker)


if __name__ == "__main__":
    main()
