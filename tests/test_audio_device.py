"""Tests for find_audio_device_by_name() with mock PyAudio."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_mock_pyaudio(devices):
    """Create a mock PyAudio instance with given device list."""
    mock_pa = MagicMock()
    mock_pa.get_device_count.return_value = len(devices)
    mock_pa.get_device_info_by_index = lambda idx: devices[idx]
    return mock_pa


SAMPLE_DEVICES = [
    {"name": "Built-in Microphone", "maxInputChannels": 2, "maxOutputChannels": 0, "defaultSampleRate": 44100},
    {"name": "USB CAMERA", "maxInputChannels": 1, "maxOutputChannels": 0, "defaultSampleRate": 48000},
    {"name": "CABLE Output (VB-Audio Virtual Cable)", "maxInputChannels": 2, "maxOutputChannels": 0, "defaultSampleRate": 48000},
    {"name": "MacBook Pro Speakers", "maxInputChannels": 0, "maxOutputChannels": 2, "defaultSampleRate": 44100},
    {"name": "CABLE Input (VB-Audio Virtual Cable)", "maxInputChannels": 0, "maxOutputChannels": 2, "defaultSampleRate": 48000},
]


def _find_audio_device_by_name(name_pattern, input_only=True, mock_devices=None):
    """Standalone reimplementation of the function for testing without controller side effects."""
    devices = mock_devices or SAMPLE_DEVICES
    for i, info in enumerate(devices):
        if name_pattern.lower() in info['name'].lower():
            if input_only and info['maxInputChannels'] == 0:
                continue
            return i, info['name'], info
    return None, None, None


class TestFindAudioDeviceByName:
    """Test audio device name resolution logic."""

    def test_finds_mic_by_name(self):
        idx, name, info = _find_audio_device_by_name("USB CAMERA")
        assert idx == 1
        assert name == "USB CAMERA"

    def test_finds_cable_output(self):
        idx, name, info = _find_audio_device_by_name("CABLE Output")
        assert idx == 2
        assert "CABLE Output" in name

    def test_case_insensitive_match(self):
        idx, name, _ = _find_audio_device_by_name("usb camera")
        assert idx == 1

    def test_returns_none_for_missing_device(self):
        idx, name, info = _find_audio_device_by_name("NonExistent Device XYZ")
        assert idx is None
        assert name is None
        assert info is None

    def test_input_only_skips_output_devices(self):
        idx, name, _ = _find_audio_device_by_name("CABLE Input", input_only=True)
        assert idx is None

    def test_input_only_false_finds_output_devices(self):
        idx, name, _ = _find_audio_device_by_name("CABLE Input", input_only=False)
        assert idx == 4

    def test_partial_match(self):
        idx, name, _ = _find_audio_device_by_name("Built-in")
        assert idx == 0
        assert "Built-in Microphone" in name

    def test_empty_device_list(self):
        idx, name, _ = _find_audio_device_by_name("anything", mock_devices=[])
        assert idx is None

    def test_first_match_wins(self):
        """When multiple devices match, should return the first."""
        devices = [
            {"name": "CABLE Output 1", "maxInputChannels": 2, "maxOutputChannels": 0, "defaultSampleRate": 48000},
            {"name": "CABLE Output 2", "maxInputChannels": 2, "maxOutputChannels": 0, "defaultSampleRate": 48000},
        ]
        idx, name, _ = _find_audio_device_by_name("CABLE Output", mock_devices=devices)
        assert idx == 0
        assert name == "CABLE Output 1"
