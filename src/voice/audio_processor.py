"""Audio processing utilities for voice cloning."""

import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import librosa

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio file processing and manipulation."""

    @staticmethod
    def load_audio(file_path: str, sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """
        Load an audio file.

        Args:
            file_path: Path to audio file
            sr: Target sample rate (None = native rate)

        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            audio, sample_rate = librosa.load(file_path, sr=sr)
            logger.info(f"Loaded audio: {file_path} ({len(audio)} samples, {sample_rate}Hz)")
            return audio, sample_rate

        except Exception as e:
            logger.error(f"Failed to load audio {file_path}: {e}")
            raise

    @staticmethod
    def save_audio(
        audio_data: np.ndarray,
        file_path: str,
        sample_rate: int = 22050
    ) -> str:
        """
        Save audio data to file.

        Args:
            audio_data: Audio samples as numpy array
            file_path: Output file path
            sample_rate: Sample rate in Hz

        Returns:
            Path to saved file
        """
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            sf.write(file_path, audio_data, sample_rate)
            logger.info(f"Saved audio: {file_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to save audio {file_path}: {e}")
            raise

    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """
        Get information about an audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio metadata
        """
        try:
            audio = AudioSegment.from_file(file_path)

            info = {
                "duration_seconds": len(audio) / 1000.0,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
                "frame_count": audio.frame_count(),
                "format": Path(file_path).suffix.lstrip('.').upper(),
                "file_size_mb": Path(file_path).stat().st_size / (1024 * 1024),
            }

            logger.debug(f"Audio info for {file_path}: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to get audio info for {file_path}: {e}")
            raise

    @staticmethod
    def trim_audio(
        file_path: str,
        output_path: str,
        start_ms: int = 0,
        end_ms: Optional[int] = None
    ) -> str:
        """
        Trim audio file to specified duration.

        Args:
            file_path: Input audio file path
            output_path: Output audio file path
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds (None = end of file)

        Returns:
            Path to trimmed audio file
        """
        try:
            audio = AudioSegment.from_file(file_path)

            if end_ms is None:
                end_ms = len(audio)

            trimmed = audio[start_ms:end_ms]

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            trimmed.export(output_path, format=output_path.suffix.lstrip('.'))

            logger.info(f"Trimmed audio: {start_ms}ms to {end_ms}ms -> {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to trim audio: {e}")
            raise

    @staticmethod
    def split_audio(
        file_path: str,
        output_dir: str,
        chunk_duration_ms: int = 60000,
        prefix: str = "chunk"
    ) -> list:
        """
        Split audio into chunks of specified duration.

        Args:
            file_path: Input audio file path
            output_dir: Output directory for chunks
            chunk_duration_ms: Duration of each chunk in milliseconds
            prefix: Prefix for chunk filenames

        Returns:
            List of paths to chunk files
        """
        try:
            audio = AudioSegment.from_file(file_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            chunks = []
            total_duration = len(audio)
            chunk_count = (total_duration // chunk_duration_ms) + 1

            for i in range(chunk_count):
                start = i * chunk_duration_ms
                end = min((i + 1) * chunk_duration_ms, total_duration)

                chunk = audio[start:end]
                chunk_path = output_dir / f"{prefix}_{i+1:03d}.mp3"

                chunk.export(chunk_path, format="mp3")
                chunks.append(str(chunk_path))

            logger.info(f"Split audio into {len(chunks)} chunks: {output_dir}")
            return chunks

        except Exception as e:
            logger.error(f"Failed to split audio: {e}")
            raise

    @staticmethod
    def convert_format(
        file_path: str,
        output_path: str,
        output_format: str = "mp3",
        bitrate: str = "192k"
    ) -> str:
        """
        Convert audio file to different format.

        Args:
            file_path: Input audio file path
            output_path: Output audio file path
            output_format: Target format (mp3, wav, etc.)
            bitrate: Target bitrate for compressed formats

        Returns:
            Path to converted file
        """
        try:
            audio = AudioSegment.from_file(file_path)

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            audio.export(
                output_path,
                format=output_format,
                bitrate=bitrate
            )

            logger.info(f"Converted {file_path} to {output_format}: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to convert audio format: {e}")
            raise

    @staticmethod
    def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1, 1] range.

        Args:
            audio_data: Audio samples

        Returns:
            Normalized audio samples
        """
        max_val = np.abs(audio_data).max()
        if max_val > 0:
            return audio_data / max_val
        return audio_data

    @staticmethod
    def detect_silence(
        file_path: str,
        min_silence_len: int = 1000,
        silence_thresh: int = -40
    ) -> list:
        """
        Detect silent sections in audio.

        Args:
            file_path: Path to audio file
            min_silence_len: Minimum silence length in ms
            silence_thresh: Silence threshold in dBFS

        Returns:
            List of (start_ms, end_ms) tuples for silent sections
        """
        try:
            from pydub.silence import detect_silence as pydub_detect_silence

            audio = AudioSegment.from_file(file_path)
            silent_sections = pydub_detect_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh
            )

            logger.info(f"Detected {len(silent_sections)} silent sections in {file_path}")
            return silent_sections

        except Exception as e:
            logger.error(f"Failed to detect silence: {e}")
            raise

    @staticmethod
    def remove_silence(
        file_path: str,
        output_path: str,
        min_silence_len: int = 1000,
        silence_thresh: int = -40,
        keep_silence: int = 100
    ) -> str:
        """
        Remove silent sections from audio.

        Args:
            file_path: Input audio file path
            output_path: Output audio file path
            min_silence_len: Minimum silence length in ms to remove
            silence_thresh: Silence threshold in dBFS
            keep_silence: Keep this much silence (ms) at detected boundaries

        Returns:
            Path to processed audio file
        """
        try:
            from pydub.silence import split_on_silence

            audio = AudioSegment.from_file(file_path)

            # Split on silence and keep non-silent chunks
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
                keep_silence=keep_silence
            )

            # Concatenate chunks
            output_audio = AudioSegment.empty()
            for chunk in chunks:
                output_audio += chunk

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_audio.export(output_path, format=output_path.suffix.lstrip('.'))

            logger.info(f"Removed silence: {file_path} -> {output_path}")
            logger.info(f"Duration: {len(audio)/1000:.1f}s -> {len(output_audio)/1000:.1f}s")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to remove silence: {e}")
            raise

    @staticmethod
    def validate_for_cloning(file_path: str) -> dict:
        """
        Validate audio file quality for voice cloning.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with validation results and recommendations
        """
        try:
            info = AudioProcessor.get_audio_info(file_path)

            validation = {
                "valid": True,
                "warnings": [],
                "info": info
            }

            # Check duration (ideally 1-5 minutes)
            duration = info['duration_seconds']
            if duration < 30:
                validation['warnings'].append(
                    f"Audio is short ({duration:.1f}s). Recommended: 60-300s for best results."
                )
            elif duration > 600:
                validation['warnings'].append(
                    f"Audio is long ({duration:.1f}s). Consider splitting into smaller chunks."
                )

            # Check sample rate (ideally 44.1kHz or higher)
            if info['sample_rate'] < 22050:
                validation['warnings'].append(
                    f"Low sample rate ({info['sample_rate']}Hz). Recommended: 44100Hz or higher."
                )

            # Check if mono/stereo
            if info['channels'] > 1:
                validation['warnings'].append(
                    "Audio is multi-channel. Consider converting to mono for voice cloning."
                )

            if not validation['warnings']:
                validation['message'] = "Audio file looks good for voice cloning!"
            else:
                validation['message'] = "Audio file has some issues (see warnings)"

            return validation

        except Exception as e:
            logger.error(f"Failed to validate audio: {e}")
            raise
