"""Pure helpers for the Deepgram Speech-to-Text integration."""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Mapping
from typing import Any

WAV_HEADER_SIZE = 44


def api_key_fingerprint(api_key: str) -> str:
    """Return a stable fingerprint without storing the API key itself."""
    return hashlib.sha256(api_key.strip().encode("utf-8")).hexdigest()


def ensure_wav(
    audio: bytes,
    *,
    sample_rate: int,
    channels: int,
    bits_per_sample: int,
) -> bytes:
    """Return RIFF/WAVE audio, adding a header to raw PCM when needed."""
    if len(audio) >= 12 and audio[:4] == b"RIFF" and audio[8:12] == b"WAVE":
        return audio

    if bits_per_sample != 16:
        raise ValueError("Only 16-bit PCM audio is supported")

    if channels not in (1, 2):
        raise ValueError("Only mono or stereo PCM audio is supported")

    block_align = channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    data_size = len(audio)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio


def extract_transcript(payload: Mapping[str, Any]) -> str:
    """Extract the first transcript from a Deepgram pre-recorded response."""
    try:
        transcript = payload["results"]["channels"][0]["alternatives"][0]["transcript"]
    except (KeyError, IndexError, TypeError) as err:
        raise ValueError("Deepgram response does not contain a transcript") from err

    if not isinstance(transcript, str):
        raise TypeError("Deepgram transcript is not a string")

    return transcript.strip()
