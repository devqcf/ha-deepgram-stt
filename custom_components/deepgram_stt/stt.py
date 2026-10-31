"""Deepgram Speech-to-Text platform."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterable

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import (
    DeepgramAPIError,
    DeepgramAuthError,
    DeepgramConnectionError,
    DeepgramRateLimitError,
    DeepgramResponseError,
    async_transcribe,
)
from .const import (
    AUDIO_COLLECT_TIMEOUT,
    CONF_API_KEY,
    CONF_MODEL,
    CONF_NUMERALS,
    CONF_PUNCTUATE,
    CONF_SMART_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_NUMERALS,
    DEFAULT_PUNCTUATE,
    DEFAULT_SMART_FORMAT,
    MAX_AUDIO_BYTES,
    SUPPORTED_LANGUAGES,
)
from .util import ensure_wav

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepgram STT entity from a config entry."""
    async_add_entities([DeepgramSTTEntity(config_entry)])


class DeepgramSTTEntity(SpeechToTextEntity):
    """A Deepgram-backed speech-to-text entity."""

    _attr_name = "Deepgram STT"
    _attr_has_entity_name = False

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the STT entity."""
        self._entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_stt"

        data = {**config_entry.data, **config_entry.options}
        model = data.get(CONF_MODEL, DEFAULT_MODEL)
        self._model = model if model in SUPPORTED_LANGUAGES else DEFAULT_MODEL
        self._smart_format = bool(data.get(CONF_SMART_FORMAT, DEFAULT_SMART_FORMAT))
        self._punctuate = bool(data.get(CONF_PUNCTUATE, DEFAULT_PUNCTUATE))
        self._numerals = bool(data.get(CONF_NUMERALS, DEFAULT_NUMERALS))
        self._languages = list(SUPPORTED_LANGUAGES[self._model])

    @property
    def supported_languages(self) -> list[str]:
        """Return languages supported by the selected model."""
        return self._languages

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return supported audio formats."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return supported audio codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return supported sample rates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return supported audio channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Transcribe an Assist audio stream with Deepgram."""
        api_key = self._entry.data.get(CONF_API_KEY, "").strip()
        if not api_key:
            _LOGGER.error("Deepgram API key is missing from the config entry")
            return SpeechResult(None, SpeechResultState.ERROR)

        try:
            audio = await self._async_collect_audio(stream)
        except TimeoutError:
            _LOGGER.error("Timed out while collecting audio from Assist")
            return SpeechResult(None, SpeechResultState.ERROR)
        except ValueError as err:
            _LOGGER.error("Invalid or oversized audio from Assist: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)

        if not audio:
            _LOGGER.debug("No audio received from Assist")
            return SpeechResult("", SpeechResultState.SUCCESS)

        try:
            wav_audio = ensure_wav(
                audio,
                sample_rate=int(metadata.sample_rate),
                channels=int(metadata.channel),
                bits_per_sample=int(metadata.bit_rate),
            )
        except ValueError as err:
            _LOGGER.error("Unsupported Assist audio format: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)

        try:
            text = await async_transcribe(
                self.hass,
                api_key,
                wav_audio,
                model=self._model,
                language=metadata.language,
                smart_format=self._smart_format,
                punctuate=self._punctuate,
                numerals=self._numerals,
            )
        except DeepgramAuthError:
            _LOGGER.warning("Deepgram authentication failed; starting reauth")
            self._entry.async_start_reauth(self.hass)
            return SpeechResult(None, SpeechResultState.ERROR)
        except DeepgramRateLimitError:
            _LOGGER.warning("Deepgram rate limit reached")
            return SpeechResult(None, SpeechResultState.ERROR)
        except DeepgramConnectionError as err:
            _LOGGER.error("Deepgram connection error: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)
        except DeepgramAPIError as err:
            _LOGGER.error("Deepgram API error: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)
        except DeepgramResponseError as err:
            _LOGGER.error("Deepgram response error: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)

        return SpeechResult(text, SpeechResultState.SUCCESS)

    async def _async_collect_audio(self, stream: AsyncIterable[bytes]) -> bytes:
        """Collect the complete utterance, with a safety limit."""
        chunks: list[bytes] = []
        total = 0

        async with asyncio.timeout(AUDIO_COLLECT_TIMEOUT):
            async for chunk in stream:
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_AUDIO_BYTES:
                    raise ValueError(f"audio exceeds {MAX_AUDIO_BYTES} bytes")
                chunks.append(chunk)

        return b"".join(chunks)
