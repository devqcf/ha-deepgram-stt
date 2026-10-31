"""Tests for the pure helpers in the Deepgram STT integration.

The helpers do not depend on Home Assistant, so they are loaded directly from
their files. This keeps the test suite runnable without installing Home
Assistant locally; CI additionally runs hassfest and HACS validation.
"""

from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relative_path: str):
    """Load a standalone module from the integration directory."""
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


const = _load("deepgram_const", "custom_components/deepgram_stt/const.py")
util = _load("deepgram_util", "custom_components/deepgram_stt/util.py")


class EnsureWavTest(unittest.TestCase):
    """Test WAV normalization."""

    def test_wraps_raw_pcm(self) -> None:
        """Raw PCM gets a valid RIFF header."""
        pcm = b"\x00\x01" * 160
        wav = util.ensure_wav(pcm, sample_rate=16000, channels=1, bits_per_sample=16)

        self.assertEqual(wav[:4], b"RIFF")
        self.assertEqual(wav[8:12], b"WAVE")
        self.assertEqual(wav[12:16], b"fmt ")
        self.assertEqual(wav[36:40], b"data")
        self.assertEqual(wav[44:], pcm)

        (riff_size,) = struct.unpack("<I", wav[4:8])
        (data_size,) = struct.unpack("<I", wav[40:44])
        self.assertEqual(riff_size, 36 + len(pcm))
        self.assertEqual(data_size, len(pcm))

        (sample_rate,) = struct.unpack("<I", wav[24:28])
        (channels,) = struct.unpack("<H", wav[22:24])
        (bits_per_sample,) = struct.unpack("<H", wav[34:36])
        self.assertEqual(sample_rate, 16000)
        self.assertEqual(channels, 1)
        self.assertEqual(bits_per_sample, 16)

    def test_keeps_existing_wav(self) -> None:
        """An existing RIFF/WAVE file is returned unchanged."""
        wav = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"payload"
        self.assertEqual(
            util.ensure_wav(wav, sample_rate=16000, channels=1, bits_per_sample=16),
            wav,
        )

    def test_supports_stereo(self) -> None:
        """Stereo raw PCM is wrapped with the correct block alignment."""
        pcm = b"\x00" * 64
        wav = util.ensure_wav(pcm, sample_rate=16000, channels=2, bits_per_sample=16)
        (block_align,) = struct.unpack("<H", wav[32:34])
        (byte_rate,) = struct.unpack("<I", wav[28:32])
        self.assertEqual(block_align, 4)
        self.assertEqual(byte_rate, 64000)

    def test_rejects_non_16_bit_audio(self) -> None:
        """Only 16-bit PCM is supported."""
        with self.assertRaises(ValueError):
            util.ensure_wav(
                b"\x00" * 32,
                sample_rate=16000,
                channels=1,
                bits_per_sample=8,
            )

    def test_rejects_too_many_channels(self) -> None:
        """More than two channels is rejected."""
        with self.assertRaises(ValueError):
            util.ensure_wav(
                b"\x00" * 32,
                sample_rate=16000,
                channels=3,
                bits_per_sample=16,
            )


class TranscriptTest(unittest.TestCase):
    """Test transcript extraction."""

    def test_extracts_and_strips_transcript(self) -> None:
        """The first alternative is returned without surrounding spaces."""
        payload = {
            "results": {
                "channels": [{"alternatives": [{"transcript": "  Привет, мир.  "}]}]
            }
        }
        self.assertEqual(util.extract_transcript(payload), "Привет, мир.")

    def test_empty_transcript(self) -> None:
        """Silence produces an empty transcript, not an error."""
        payload = {"results": {"channels": [{"alternatives": [{"transcript": ""}]}]}}
        self.assertEqual(util.extract_transcript(payload), "")

    def test_missing_transcript_raises(self) -> None:
        """Malformed responses raise ValueError."""
        with self.assertRaises(ValueError):
            util.extract_transcript({"results": {}})

    def test_non_string_transcript_raises(self) -> None:
        """A non-string transcript is rejected."""
        payload = {"results": {"channels": [{"alternatives": [{"transcript": None}]}]}}
        with self.assertRaises(TypeError):
            util.extract_transcript(payload)


class FingerprintTest(unittest.TestCase):
    """Test API-key fingerprinting."""

    def test_fingerprint_is_stable_and_not_the_key(self) -> None:
        """The fingerprint is deterministic and does not reveal the key."""
        key = "example-key-value"
        fingerprint = util.api_key_fingerprint(key)
        self.assertEqual(fingerprint, util.api_key_fingerprint(f"  {key}  "))
        self.assertNotIn(key, fingerprint)
        self.assertEqual(len(fingerprint), 64)

    def test_fingerprints_differ(self) -> None:
        """Different keys produce different fingerprints."""
        self.assertNotEqual(
            util.api_key_fingerprint("key-one"),
            util.api_key_fingerprint("key-two"),
        )


class LanguageTest(unittest.TestCase):
    """Test the advertised language lists."""

    def test_russian_is_supported_by_both_models(self) -> None:
        """Russian is mandatory and available in each model."""
        self.assertIn("ru", const.NOVA3_LANGUAGES)
        self.assertIn("ru", const.NOVA2_LANGUAGES)
        for model in const.MODELS:
            self.assertIn("ru", const.SUPPORTED_LANGUAGES[model])

    def test_default_model_is_supported(self) -> None:
        """The default model has a language list."""
        self.assertIn(const.DEFAULT_MODEL, const.SUPPORTED_LANGUAGES)

    def test_language_lists_are_unique(self) -> None:
        """No duplicate tags in the advertised lists."""
        for languages in const.SUPPORTED_LANGUAGES.values():
            self.assertEqual(len(languages), len(set(languages)))


if __name__ == "__main__":
    unittest.main()
