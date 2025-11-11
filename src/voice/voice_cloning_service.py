"""Voice cloning service - high-level interface for voice cloning operations."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from src.voice.elevenlabs_client import ElevenLabsClient
from src.voice.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class VoiceCloningService:
    """
    High-level service for voice cloning operations.

    Combines ElevenLabs API client and audio processing utilities
    to provide a simple interface for voice cloning workflows.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize voice cloning service.

        Args:
            api_key: ElevenLabs API key (optional, reads from env if not provided)
        """
        self.client = ElevenLabsClient(api_key)
        self.processor = AudioProcessor()
        logger.info("Voice cloning service initialized")

    def clone_voice_from_audio(
        self,
        name: str,
        audio_files: List[str],
        description: Optional[str] = None,
        validate: bool = True,
        auto_process: bool = False
    ) -> str:
        """
        Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            audio_files: List of audio file paths
            description: Optional description
            validate: Whether to validate audio quality
            auto_process: Whether to auto-process audio (remove silence, normalize)

        Returns:
            voice_id: ID of the cloned voice
        """
        try:
            logger.info(f"Starting voice cloning for '{name}' with {len(audio_files)} files")

            # Validate audio files if requested
            if validate:
                for audio_file in audio_files:
                    validation = self.processor.validate_for_cloning(audio_file)
                    if validation['warnings']:
                        logger.warning(f"Audio validation warnings for {audio_file}:")
                        for warning in validation['warnings']:
                            logger.warning(f"  - {warning}")

            # Auto-process audio if requested
            processed_files = audio_files
            if auto_process:
                processed_files = []
                for i, audio_file in enumerate(audio_files):
                    # Remove silence and save to temp file
                    temp_path = Path("data/audio/temp") / f"processed_{i}_{Path(audio_file).name}"
                    processed = self.processor.remove_silence(
                        audio_file,
                        str(temp_path),
                        min_silence_len=500,
                        silence_thresh=-45
                    )
                    processed_files.append(processed)
                logger.info(f"Auto-processed {len(processed_files)} audio files")

            # Clone the voice
            voice_id = self.client.clone_voice(
                name=name,
                audio_files=processed_files,
                description=description
            )

            logger.info(f"Voice cloned successfully: {voice_id}")
            return voice_id

        except Exception as e:
            logger.error(f"Failed to clone voice: {e}")
            raise

    def generate_speech(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        **kwargs
    ) -> str:
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            voice_id: ID of voice to use
            output_path: Where to save the audio
            **kwargs: Additional arguments for generation (stability, similarity_boost, etc.)

        Returns:
            Path to generated audio file
        """
        try:
            logger.info(f"Generating speech: {len(text)} characters")

            result = self.client.generate_speech(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                **kwargs
            )

            logger.info(f"Speech generated: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            raise

    def quick_clone_and_speak(
        self,
        voice_name: str,
        audio_files: List[str],
        text: str,
        output_path: str,
        description: Optional[str] = None,
        **generation_kwargs
    ) -> Dict[str, Any]:
        """
        Quick workflow: Clone voice and generate speech in one call.

        Args:
            voice_name: Name for the cloned voice
            audio_files: Audio samples for cloning
            text: Text to speak
            output_path: Where to save the generated speech
            description: Voice description
            **generation_kwargs: Arguments for speech generation

        Returns:
            Dictionary with voice_id and audio_path
        """
        try:
            logger.info(f"Quick clone and speak workflow for '{voice_name}'")

            # Clone the voice
            voice_id = self.clone_voice_from_audio(
                name=voice_name,
                audio_files=audio_files,
                description=description,
                validate=True,
                auto_process=True
            )

            # Generate speech
            audio_path = self.generate_speech(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                **generation_kwargs
            )

            result = {
                "voice_id": voice_id,
                "audio_path": audio_path,
                "voice_name": voice_name
            }

            logger.info(f"Quick clone and speak completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Quick clone and speak failed: {e}")
            raise

    def list_available_voices(self) -> List[Dict[str, Any]]:
        """
        List all available voices (preset + cloned).

        Returns:
            List of voice information dictionaries
        """
        return self.client.list_voices()

    def delete_cloned_voice(self, voice_id: str) -> bool:
        """
        Delete a cloned voice.

        Args:
            voice_id: ID of voice to delete

        Returns:
            True if successful
        """
        return self.client.delete_voice(voice_id)

    def prepare_audio_for_cloning(
        self,
        input_file: str,
        output_dir: str,
        remove_silence: bool = True,
        split_if_long: bool = True,
        max_duration_seconds: int = 300
    ) -> List[str]:
        """
        Prepare audio file(s) for optimal voice cloning.

        Args:
            input_file: Path to input audio file
            output_dir: Directory for processed files
            remove_silence: Whether to remove silent sections
            split_if_long: Whether to split long audio
            max_duration_seconds: Max duration per chunk

        Returns:
            List of processed audio file paths
        """
        try:
            logger.info(f"Preparing audio for cloning: {input_file}")

            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get audio info
            info = self.processor.get_audio_info(input_file)
            duration = info['duration_seconds']

            processed_files = []

            # Remove silence if requested
            if remove_silence:
                silence_removed_path = output_dir / f"no_silence_{Path(input_file).name}"
                input_file = self.processor.remove_silence(
                    input_file,
                    str(silence_removed_path)
                )
                # Update duration after silence removal
                info = self.processor.get_audio_info(input_file)
                duration = info['duration_seconds']

            # Split if too long
            if split_if_long and duration > max_duration_seconds:
                chunk_duration_ms = max_duration_seconds * 1000
                chunks = self.processor.split_audio(
                    input_file,
                    str(output_dir),
                    chunk_duration_ms=chunk_duration_ms,
                    prefix="prepared"
                )
                processed_files.extend(chunks)
                logger.info(f"Split long audio into {len(chunks)} chunks")
            else:
                # Just copy/use the processed file
                processed_files.append(input_file)

            logger.info(f"Audio preparation complete: {len(processed_files)} files")
            return processed_files

        except Exception as e:
            logger.error(f"Failed to prepare audio: {e}")
            raise
