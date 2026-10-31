"""Constants for the Deepgram Speech-to-Text integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "deepgram_stt"
INTEGRATION_NAME: Final = "Deepgram Speech-to-Text"

API_URL: Final = "https://api.deepgram.com/v1/listen"
AUTH_URL: Final = "https://api.deepgram.com/v1/auth/token"

CONF_API_KEY: Final = "api_key"
CONF_MODEL: Final = "model"
CONF_NUMERALS: Final = "numerals"
CONF_PUNCTUATE: Final = "punctuate"
CONF_SMART_FORMAT: Final = "smart_format"

DEFAULT_MODEL: Final = "nova-3"
DEFAULT_NUMERALS: Final = True
DEFAULT_PUNCTUATE: Final = True
DEFAULT_SMART_FORMAT: Final = True

MODEL_NOVA2: Final = "nova-2"
MODEL_NOVA3: Final = "nova-3"
MODELS: Final = (MODEL_NOVA3, MODEL_NOVA2)

# Deepgram supports more regional variants than are useful in the Assist UI.
# The base language tags below are accepted by the corresponding model and are
# matched by Home Assistant's language utilities.
NOVA3_LANGUAGES: Final = (
    "af",
    "ar",
    "as",
    "be",
    "bn",
    "bs",
    "bg",
    "ca",
    "zh",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "et",
    "fi",
    "fr",
    "de",
    "el",
    "gl",
    "gu",
    "he",
    "hi",
    "hu",
    "hy",
    "id",
    "it",
    "ja",
    "ka",
    "kk",
    "kn",
    "ko",
    "lv",
    "lt",
    "mk",
    "mn",
    "mr",
    "ms",
    "ne",
    "no",
    "fa",
    "pa",
    "pl",
    "ps",
    "pt",
    "ro",
    "ru",
    "sr",
    "sk",
    "sl",
    "es",
    "sv",
    "tl",
    "ta",
    "te",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
    "xh",
    "zu",
)

NOVA2_LANGUAGES: Final = (
    "bg",
    "ca",
    "zh",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "et",
    "fi",
    "fr",
    "de",
    "el",
    "hi",
    "hu",
    "id",
    "it",
    "ja",
    "ko",
    "lv",
    "lt",
    "ms",
    "no",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "es",
    "sv",
    "th",
    "tr",
    "uk",
    "vi",
)

SUPPORTED_LANGUAGES: Final = {
    MODEL_NOVA3: NOVA3_LANGUAGES,
    MODEL_NOVA2: NOVA2_LANGUAGES,
}

AUDIO_COLLECT_TIMEOUT: Final = 60
API_TIMEOUT: Final = 30
MAX_AUDIO_BYTES: Final = 20 * 1024 * 1024

SAMPLE_RATE: Final = 16000
SAMPLE_WIDTH: Final = 2
CHANNELS: Final = 1
