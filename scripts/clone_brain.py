#!/usr/bin/env python3
"""
Clone Brain - LLM-powered responses for the digital clone

This script connects to GPT-5.1 (no-reasoning mode for speed) to generate
contextual responses for the clone during a video interview.

The clone is a digital replica of Jason Tulloch, speaking to Jason in a
Google Meet call where Jason is interviewing Robert Cordwell for a forward
deployed engineering role at Giga.

Usage:
    python clone_brain.py                     # Interactive mode
    python clone_brain.py --speak             # Also speaks responses via OBS
    python clone_brain.py --prompt "Hello"    # One-shot response

Architecture:
    User types context/question
           |
           v
    clone_brain.py (GPT-5.1 no-reasoning)
           |
           v
    Response (5-20 seconds to speak)
           |
           v
    clone_speaker_obs.py (ElevenLabs TTS -> OBS -> Meet)
"""

import os
import sys
from pathlib import Path
from openai import OpenAI

# Load environment
from dotenv import load_dotenv
# Load from config-specified env file, then fall back to project .env
_master_env = Path.home() / "iCloudDrive" / "Documents" / "Projects" / "ClaudeCommander" / "master.env"
if _master_env.exists():
    load_dotenv(_master_env)
else:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Load system prompt from config file
_project_root = Path(__file__).resolve().parent.parent
_system_prompt_file = _project_root / "config" / "clone_system_prompt.txt"

if _system_prompt_file.exists():
    FULL_SYSTEM_PROMPT = _system_prompt_file.read_text(encoding="utf-8")
else:
    FULL_SYSTEM_PROMPT = "You are a helpful AI assistant in a video call interview context."
    print(f"WARNING: System prompt file not found: {_system_prompt_file}")

# Brain model from config
sys.path.insert(0, str(_project_root))
try:
    from src.utils.config_loader import ConfigLoader
    _config = ConfigLoader(str(_project_root / "config" / "config.yaml"))
    BRAIN_MODEL = _config.get("brain", "model", default="gpt-5.1")
    FALLBACK_MODEL = _config.get("brain", "fallback_model", default="gpt-4o")
    MAX_HISTORY = _config.get("brain", "max_history", default=20)
except Exception:
    BRAIN_MODEL = "gpt-5.1"
    FALLBACK_MODEL = "gpt-4o"
    MAX_HISTORY = 20


class CloneBrain:
    """LLM-powered brain for the digital clone."""

    def __init__(self, speak: bool = False):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.conversation_history = []
        self.speak = speak
        self.speaker = None

        if speak:
            # Import the OBS speaker (same directory)
            from clone_speaker_obs import CloneSpeakerOBS
            self.speaker = CloneSpeakerOBS()

    def think(self, user_input: str) -> str:
        """Generate a response to the user input.

        Args:
            user_input: What was said/asked in the interview

        Returns:
            The clone's response (5-20 seconds to speak)
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Trim history if too long
        if len(self.conversation_history) > MAX_HISTORY:
            self.conversation_history = self.conversation_history[-MAX_HISTORY:]

        # Call LLM for response
        try:
            response = self.client.chat.completions.create(
                model=BRAIN_MODEL,
                messages=[
                    {"role": "system", "content": FULL_SYSTEM_PROMPT},
                    *self.conversation_history
                ],
                max_tokens=150,
                temperature=0.8,
            )
        except Exception as e:
            print(f"Primary model ({BRAIN_MODEL}) failed: {e}, trying fallback...")
            response = self.client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[
                    {"role": "system", "content": FULL_SYSTEM_PROMPT},
                    *self.conversation_history
                ],
                max_tokens=150,
                temperature=0.8,
            )

        assistant_message = response.choices[0].message.content

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def respond(self, user_input: str) -> str:
        """Generate and optionally speak a response."""
        response = self.think(user_input)

        if self.speak and self.speaker:
            print(f"\n[Speaking...]")
            self.speaker.speak(response, wait=True)

        return response

    def reset_conversation(self):
        """Clear conversation history for a fresh start."""
        self.conversation_history = []


def interactive_mode(brain: CloneBrain):
    """Interactive mode for the interview."""
    print("\n" + "="*70)
    print("CLONE BRAIN - Digital Replica of Jason Tulloch")
    print("="*70)
    print("Context: Interview with Robert Cordwell for FDE role at Giga")
    print("Objective: Advocate for Robert based on Slopify project")
    print()
    print("Type what's happening in the interview, or questions for the clone.")
    print("Commands: /quit, /reset, /speak (toggle), /context")
    print("="*70 + "\n")

    speak_enabled = brain.speak

    while True:
        try:
            prompt = input("\n[Interview] > ").strip()

            if not prompt:
                continue

            if prompt == "/quit":
                print("Session ended.")
                break

            if prompt == "/reset":
                brain.reset_conversation()
                print("Conversation reset. Fresh start.")
                continue

            if prompt == "/speak":
                speak_enabled = not speak_enabled
                brain.speak = speak_enabled
                if speak_enabled and not brain.speaker:
                    from clone_speaker_obs import CloneSpeakerOBS
                    brain.speaker = CloneSpeakerOBS()
                print(f"Speech output: {'ON' if speak_enabled else 'OFF'}")
                continue

            if prompt == "/context":
                print("\n--- SYSTEM PROMPT ---")
                print(FULL_SYSTEM_PROMPT[:2000] + "...")
                print("--- END ---\n")
                continue

            # Get response
            print("\n[Clone thinking...]")
            response = brain.respond(prompt)
            print(f"\n[Clone]: {response}")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clone Brain - LLM for digital replica")
    parser.add_argument("--speak", action="store_true", help="Also speak responses via OBS")
    parser.add_argument("--prompt", type=str, help="One-shot: respond to this and exit")

    args = parser.parse_args()

    try:
        brain = CloneBrain(speak=args.speak)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.prompt:
        response = brain.respond(args.prompt)
        print(response)
        return

    interactive_mode(brain)


if __name__ == "__main__":
    main()
