#!/usr/bin/env python3
"""CLI tool for voice cloning operations."""

import sys
import click
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / ".env")

from src.voice.voice_cloning_service import VoiceCloningService
from src.utils.logger import setup_logger

logger = setup_logger("clone_voice", level="INFO", console=True)


@click.group()
def cli():
    """Voice cloning CLI tool."""
    pass


@cli.command()
@click.option("--name", required=True, help="Name for the cloned voice")
@click.option("--audio", "-a", multiple=True, required=True, help="Audio file(s) for cloning (can specify multiple)")
@click.option("--description", "-d", default=None, help="Description of the voice")
@click.option("--no-validate", is_flag=True, help="Skip audio validation")
@click.option("--auto-process", is_flag=True, help="Auto-process audio (remove silence, normalize)")
def clone(name, audio, description, no_validate, auto_process):
    """Clone a voice from audio samples."""
    try:
        click.echo(f"Cloning voice '{name}' from {len(audio)} audio file(s)...")

        service = VoiceCloningService()

        voice_id = service.clone_voice_from_audio(
            name=name,
            audio_files=list(audio),
            description=description,
            validate=not no_validate,
            auto_process=auto_process
        )

        click.echo(f"✓ Voice cloned successfully!")
        click.echo(f"  Voice ID: {voice_id}")
        click.echo(f"  Voice Name: {name}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--text", "-t", required=True, help="Text to convert to speech")
@click.option("--voice-id", required=True, help="Voice ID to use")
@click.option("--output", "-o", required=True, help="Output audio file path")
@click.option("--stability", default=0.5, type=float, help="Voice stability (0.0-1.0)")
@click.option("--similarity", default=0.75, type=float, help="Similarity boost (0.0-1.0)")
def speak(text, voice_id, output, stability, similarity):
    """Generate speech from text using a voice."""
    try:
        click.echo(f"Generating speech ({len(text)} characters)...")

        service = VoiceCloningService()

        audio_path = service.generate_speech(
            text=text,
            voice_id=voice_id,
            output_path=output,
            stability=stability,
            similarity_boost=similarity
        )

        click.echo(f"✓ Speech generated successfully!")
        click.echo(f"  Output: {audio_path}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--name", required=True, help="Name for the cloned voice")
@click.option("--audio", "-a", multiple=True, required=True, help="Audio file(s) for cloning")
@click.option("--text", "-t", required=True, help="Text to speak")
@click.option("--output", "-o", required=True, help="Output audio file path")
@click.option("--description", "-d", default=None, help="Voice description")
@click.option("--stability", default=0.5, type=float, help="Voice stability (0.0-1.0)")
@click.option("--similarity", default=0.75, type=float, help="Similarity boost (0.0-1.0)")
def quick(name, audio, text, output, description, stability, similarity):
    """Quick workflow: Clone voice and generate speech in one command."""
    try:
        click.echo(f"Quick clone and speak for '{name}'...")
        click.echo(f"  Audio files: {len(audio)}")
        click.echo(f"  Text length: {len(text)} characters")

        service = VoiceCloningService()

        result = service.quick_clone_and_speak(
            voice_name=name,
            audio_files=list(audio),
            text=text,
            output_path=output,
            description=description,
            stability=stability,
            similarity_boost=similarity
        )

        click.echo(f"✓ Success!")
        click.echo(f"  Voice ID: {result['voice_id']}")
        click.echo(f"  Audio: {result['audio_path']}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_voices():
    """List all available voices."""
    try:
        service = VoiceCloningService()
        voices = service.list_available_voices()

        click.echo(f"Available voices: {len(voices)}\n")

        for voice in voices:
            click.echo(f"  • {voice['name']}")
            click.echo(f"    ID: {voice['voice_id']}")
            if voice.get('category'):
                click.echo(f"    Category: {voice['category']}")
            if voice.get('description'):
                click.echo(f"    Description: {voice['description']}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--voice-id", required=True, help="Voice ID to delete")
@click.confirmation_option(prompt="Are you sure you want to delete this voice?")
def delete(voice_id):
    """Delete a cloned voice."""
    try:
        service = VoiceCloningService()
        service.delete_cloned_voice(voice_id)

        click.echo(f"✓ Voice deleted: {voice_id}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--input", "-i", required=True, help="Input audio file")
@click.option("--output-dir", "-o", required=True, help="Output directory for processed files")
@click.option("--remove-silence", is_flag=True, default=True, help="Remove silent sections")
@click.option("--split", is_flag=True, default=True, help="Split long audio into chunks")
@click.option("--max-duration", default=300, type=int, help="Max duration per chunk (seconds)")
def prepare(input, output_dir, remove_silence, split, max_duration):
    """Prepare audio file for optimal voice cloning."""
    try:
        click.echo(f"Preparing audio: {input}")

        service = VoiceCloningService()

        processed_files = service.prepare_audio_for_cloning(
            input_file=input,
            output_dir=output_dir,
            remove_silence=remove_silence,
            split_if_long=split,
            max_duration_seconds=max_duration
        )

        click.echo(f"✓ Audio prepared successfully!")
        click.echo(f"  Processed files: {len(processed_files)}")
        for i, file in enumerate(processed_files, 1):
            click.echo(f"    {i}. {file}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--input", "-i", required=True, help="Audio file to validate")
def validate(input):
    """Validate audio file quality for voice cloning."""
    try:
        from src.voice.audio_processor import AudioProcessor

        click.echo(f"Validating audio: {input}\n")

        processor = AudioProcessor()
        validation = processor.validate_for_cloning(input)

        # Display info
        info = validation['info']
        click.echo("Audio Information:")
        click.echo(f"  Duration: {info['duration_seconds']:.1f} seconds")
        click.echo(f"  Sample Rate: {info['sample_rate']} Hz")
        click.echo(f"  Channels: {info['channels']}")
        click.echo(f"  Format: {info['format']}")
        click.echo(f"  File Size: {info['file_size_mb']:.2f} MB")
        click.echo()

        # Display validation result
        if validation['warnings']:
            click.echo("⚠ Warnings:")
            for warning in validation['warnings']:
                click.echo(f"  • {warning}")
        else:
            click.echo("✓ Audio file looks good for voice cloning!")

        click.echo(f"\n{validation['message']}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
