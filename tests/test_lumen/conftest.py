"""Phase Lumen test fixtures and configuration."""

import pytest
from pathlib import Path

# Test fixture directory (audio samples downloaded separately, gitignored)
FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir():
    """Return the fixture directory path."""
    return FIXTURE_DIR


@pytest.fixture
def sample_wav(tmp_path):
    """Generate a minimal valid WAV file for testing."""
    import struct
    import wave

    filepath = tmp_path / "test_sample.wav"
    with wave.open(str(filepath), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        # 1 second of silence (16000 samples of 16-bit zeros)
        wav.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))
    return filepath


@pytest.fixture
def sample_wav_with_tone(tmp_path):
    """Generate a WAV file with a 440Hz tone (1 second)."""
    import math
    import struct
    import wave

    filepath = tmp_path / "test_tone.wav"
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0
    num_samples = int(sample_rate * duration)

    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)

    with wave.open(str(filepath), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *samples))
    return filepath


@pytest.fixture
def corrupt_file(tmp_path):
    """Generate a file with a valid extension but invalid content."""
    filepath = tmp_path / "corrupt.mp3"
    filepath.write_bytes(b"\x00\x01\x02\x03" * 100)
    return filepath


@pytest.fixture
def empty_file(tmp_path):
    """Generate an empty file."""
    filepath = tmp_path / "empty.wav"
    filepath.write_bytes(b"")
    return filepath


@pytest.fixture
def oversized_filename(tmp_path):
    """Generate a file with a very long filename."""
    name = "a" * 250 + ".wav"
    filepath = tmp_path / name
    filepath.write_bytes(b"\x00" * 100)
    return filepath


@pytest.fixture
def unicode_filename(tmp_path):
    """Generate a file with Unicode characters in the name."""
    import struct
    import wave

    filepath = tmp_path / "test_audio_日本語_中文_العربية.wav"
    with wave.open(str(filepath), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))
    return filepath
