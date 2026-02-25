#!/usr/bin/env python3
"""
Clone Speaker with OBS Audio Integration

Uses OBS as the audio mixer:
1. OBS captures your mic
2. This script plays TTS through a media source in OBS
3. OBS outputs the mixed audio to its Virtual Camera/Audio

This way, Google Meet gets both your voice AND the clone's voice through
OBS's virtual output.

Setup required in OBS:
1. Add your mic as an Audio Input Capture source
2. Create a Media Source called "CloneTTS" (this script will control it)
3. Enable "Monitor and Output" on the CloneTTS source
4. Use OBS Virtual Camera or VB-Cable for Meet input

Usage:
    python clone_speaker_obs.py              # Interactive mode
    python clone_speaker_obs.py --say "Hi"   # One-shot speech
"""

import os
import sys
import time
from pathlib import Path

# Load environment
from dotenv import load_dotenv
_master_env = Path.home() / "iCloudDrive" / "Documents" / "Projects" / "ClaudeCommander" / "master.env"
if _master_env.exists():
    load_dotenv(_master_env)
else:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import obsws_python as obs

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1"

# Load config
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
try:
    from src.utils.config_loader import ConfigLoader
    _config = ConfigLoader(str(_project_root / "config" / "config.yaml"))
    OBS_HOST = _config.get("obs", "host", default="localhost")
    OBS_PORT = _config.get("obs", "port", default=4455)
    OBS_PASSWORD = _config.get("obs", "password", default="slopifywins")
    DEFAULT_VOICE_ID = _config.get("tts", "voice_id", default="nf18MnSL81anCHgQgL1A")
except Exception:
    OBS_HOST = "localhost"
    OBS_PORT = 4455
    OBS_PASSWORD = "slopifywins"
    DEFAULT_VOICE_ID = "nf18MnSL81anCHgQgL1A"

TTS_SOURCE_NAME = "CloneTTS"

# Directory for TTS audio files
TTS_AUDIO_DIR = Path.home() / "clone_videos" / "tts_audio"
TTS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class CloneSpeakerOBS:
    """Speaks through OBS by controlling a media source."""

    def __init__(self, voice_id: str = DEFAULT_VOICE_ID,
                 stability: float = 0.5, similarity_boost: float = 0.75):
        self.voice_id = voice_id
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.obs_client = None
        self.current_audio_file = None

        if not ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY not set")

    def connect_obs(self):
        """Connect to OBS WebSocket."""
        if not self.obs_client:
            self.obs_client = obs.ReqClient(
                host=OBS_HOST,
                port=OBS_PORT,
                password=OBS_PASSWORD
            )
        return self.obs_client

    def ensure_tts_source(self):
        """Ensure the CloneTTS media source exists in OBS."""
        cl = self.connect_obs()

        try:
            inputs = cl.get_input_list()
            source_exists = any(i['inputName'] == TTS_SOURCE_NAME for i in inputs.inputs)

            if not source_exists:
                scenes = cl.get_scene_list()
                current_scene = scenes.current_program_scene_name

                cl.create_input(
                    sceneName=current_scene,
                    inputName=TTS_SOURCE_NAME,
                    inputKind="ffmpeg_source",
                    inputSettings={
                        "local_file": "",
                        "looping": False,
                        "restart_on_activate": True,
                    },
                    sceneItemEnabled=True,
                )
                print(f"Created {TTS_SOURCE_NAME} source in OBS")

        except Exception as e:
            print(f"Warning: Could not verify TTS source: {e}")

    def generate_speech(self, text: str) -> str:
        """Generate speech and save to file. Returns file path."""
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

        # Save to file with timestamp
        filename = f"tts_{int(time.time())}.mp3"
        filepath = TTS_AUDIO_DIR / filename

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        return str(filepath)

    def speak(self, text: str, wait: bool = True):
        """Make the clone speak through OBS."""
        print(f"  [Generating: \"{text[:50]}{'...' if len(text) > 50 else ''}\"]")

        start = time.time()
        audio_path = self.generate_speech(text)
        gen_time = time.time() - start
        print(f"  [Generated in {gen_time:.1f}s: {audio_path}]")

        cl = self.connect_obs()

        try:
            cl.set_input_settings(
                inputName=TTS_SOURCE_NAME,
                inputSettings={
                    "local_file": audio_path,
                    "restart_on_activate": True,
                },
                overlay=True
            )

            cl.trigger_media_input_action(
                inputName=TTS_SOURCE_NAME,
                mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
            )

            print(f"  [Playing through OBS: {TTS_SOURCE_NAME}]")

            if wait:
                estimated_duration = len(text) * 0.08 + 0.5
                time.sleep(estimated_duration)

        except Exception as e:
            print(f"  [OBS error: {e}]")
            raise

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

    def cleanup_old_files(self, keep_last: int = 5):
        """Remove old TTS audio files, keeping the most recent ones."""
        files = sorted(TTS_AUDIO_DIR.glob("tts_*.mp3"), key=os.path.getmtime)
        for f in files[:-keep_last]:
            try:
                os.unlink(f)
            except:
                pass


def interactive_mode(speaker: CloneSpeakerOBS):
    """Interactive mode for typing what the clone says."""
    print("\n" + "="*60)
    print("CLONE SPEAKER (OBS Mode)")
    print("="*60)
    print(f"Voice: {speaker.voice_id}")
    print(f"OBS Source: {TTS_SOURCE_NAME}")
    print("\nType what the clone should say, press Enter to speak.")
    print("Commands: /quit, /voice, /set ID")
    print("="*60 + "\n")

    try:
        speaker.ensure_tts_source()
    except Exception as e:
        print(f"Warning: OBS setup issue: {e}")

    while True:
        try:
            text = input("Clone> ").strip()

            if not text:
                continue

            if text == "/quit":
                break

            if text == "/voice":
                print("\nAvailable voices:")
                for v in speaker.list_voices():
                    marker = " *" if v['voice_id'] == speaker.voice_id else ""
                    print(f"  {v['voice_id'][:12]}... {v['name']}{marker}")
                print()
                continue

            if text.startswith("/set "):
                speaker.voice_id = text[5:].strip()
                print(f"Voice set to: {speaker.voice_id}")
                continue

            speaker.speak(text)
            speaker.cleanup_old_files()

        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def setup_obs_audio():
    """Print instructions for OBS audio setup."""
    print("""
OBS AUDIO SETUP FOR CLONE SPEAKER
==================================

1. In OBS, add an Audio Input Capture for your microphone

2. Create a Media Source called "CloneTTS":
   - Right-click Sources > Add > Media Source
   - Name it exactly: CloneTTS
   - Leave the file path empty for now
   - Uncheck "Loop"

3. Set up audio monitoring for CloneTTS:
   - Edit > Advanced Audio Properties
   - For CloneTTS: Set "Audio Monitoring" to "Monitor and Output"
   - This makes the TTS audio play locally AND go to the output

4. For Google Meet, use one of these options:

   OPTION A: OBS Virtual Camera (easiest)
   - OBS Virtual Camera includes audio
   - In Meet: Select "OBS Virtual Camera" as both camera AND microphone

   OPTION B: VB-Cable (more flexible)
   - Install VB-Cable: https://vb-audio.com/Cable/
   - In OBS Settings > Audio:
     - Set "Monitoring Device" to "CABLE Input (VB-Audio)"
   - In Google Meet:
     - Set microphone to "CABLE Output (VB-Audio)"

5. Test by running: python clone_speaker_obs.py --say "Hello"
   You should hear it AND it should appear in Meet.
""")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clone Speaker with OBS audio routing")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID, help="ElevenLabs voice ID")
    parser.add_argument("--list", action="store_true", help="List available voices")
    parser.add_argument("--say", type=str, help="Speak this text and exit")
    parser.add_argument("--setup", action="store_true", help="Show OBS setup instructions")
    parser.add_argument("--stability", type=float, default=0.5)
    parser.add_argument("--similarity", type=float, default=0.75)

    args = parser.parse_args()

    if args.setup:
        setup_obs_audio()
        return

    try:
        speaker = CloneSpeakerOBS(
            voice_id=args.voice,
            stability=args.stability,
            similarity_boost=args.similarity
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.list:
        print("\nAvailable voices:")
        for v in speaker.list_voices():
            print(f"  [{v['voice_id']}] {v['name']}")
        return

    if args.say:
        speaker.speak(args.say)
        return

    interactive_mode(speaker)


if __name__ == "__main__":
    main()
