"""Minimal Deepgram pre-recorded API client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_TIMEOUT, API_URL, AUTH_URL
from .util import extract_transcript

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "ha-deepgram-stt/1.0.0"


class DeepgramError(Exception):
    """Base error for Deepgram requests."""


class DeepgramAuthError(DeepgramError):
    """Raised when Deepgram rejects the API key."""


class DeepgramConnectionError(DeepgramError):
    """Raised when Deepgram cannot be reached."""


class DeepgramResponseError(DeepgramError):
    """Raised when Deepgram returns an unexpected response."""


class DeepgramRateLimitError(DeepgramError):
    """Raised when Deepgram rate limits the request."""


class DeepgramAPIError(DeepgramError):
    """Raised for a non-success HTTP response from Deepgram."""

    def __init__(self, status: int, message: str) -> None:
        """Initialize the API error."""
        super().__init__(f"Deepgram API returned HTTP {status}: {message}")
        self.status = status
        self.message = message


async def _error_message(response: aiohttp.ClientResponse) -> str:
    """Return a short error message without exposing request credentials."""
    try:
        payload: Any = await response.json(content_type=None)
    except (ValueError, TypeError):
        return response.reason or "Unknown error"

    if not isinstance(payload, dict):
        return response.reason or "Unknown error"

    for key in ("err_msg", "error", "message", "detail"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value[:500]

    return response.reason or "Unknown error"


def _headers(api_key: str) -> dict[str, str]:
    """Return common Deepgram request headers."""
    return {
        "Authorization": f"Token {api_key.strip()}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


async def async_validate_api_key(hass: HomeAssistant, api_key: str) -> None:
    """Validate an API key against Deepgram without transcribing audio."""
    session = async_get_clientsession(hass)
    timeout = aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10)

    try:
        async with session.get(
            AUTH_URL, headers=_headers(api_key), timeout=timeout
        ) as response:
            if response.status in (401, 403):
                raise DeepgramAuthError("Deepgram rejected the API key")

            if response.status == 429:
                raise DeepgramRateLimitError("Deepgram rate limit reached")

            if response.status >= 400:
                raise DeepgramAPIError(response.status, await _error_message(response))
    except (aiohttp.ClientError, TimeoutError) as err:
        raise DeepgramConnectionError("Unable to connect to Deepgram") from err


async def async_transcribe(
    hass: HomeAssistant,
    api_key: str,
    audio: bytes,
    *,
    model: str,
    language: str,
    smart_format: bool,
    punctuate: bool,
    numerals: bool,
) -> str:
    """Transcribe WAV audio with Deepgram's pre-recorded endpoint."""
    session = async_get_clientsession(hass)
    timeout = aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10)
    params = {
        "model": model,
        "language": language or "en",
        "smart_format": str(smart_format).lower(),
        "punctuate": str(punctuate).lower(),
        "numerals": str(numerals).lower(),
    }
    headers = _headers(api_key)
    headers["Content-Type"] = "audio/wav"

    try:
        async with session.post(
            API_URL,
            params=params,
            data=audio,
            headers=headers,
            timeout=timeout,
        ) as response:
            if response.status in (401, 403):
                raise DeepgramAuthError("Deepgram rejected the API key")

            if response.status == 429:
                raise DeepgramRateLimitError("Deepgram rate limit reached")

            if response.status >= 400:
                raise DeepgramAPIError(response.status, await _error_message(response))

            try:
                payload = await response.json(content_type=None)
            except (ValueError, TypeError) as err:
                raise DeepgramResponseError("Deepgram returned invalid JSON") from err

    except (aiohttp.ClientError, TimeoutError) as err:
        raise DeepgramConnectionError("Unable to connect to Deepgram") from err

    if not isinstance(payload, dict):
        raise DeepgramResponseError("Deepgram returned an unexpected response")

    try:
        transcript = extract_transcript(payload)
    except (TypeError, ValueError) as err:
        raise DeepgramResponseError(str(err)) from err

    _LOGGER.debug(
        "Deepgram transcription complete (model=%s, language=%s, chars=%d)",
        model,
        language,
        len(transcript),
    )
    return transcript
