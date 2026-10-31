"""Config flow for the Deepgram Speech-to-Text integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    DeepgramAPIError,
    DeepgramAuthError,
    DeepgramConnectionError,
    DeepgramRateLimitError,
    async_validate_api_key,
)
from .const import (
    CONF_API_KEY,
    CONF_MODEL,
    CONF_NUMERALS,
    CONF_PUNCTUATE,
    CONF_SMART_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_NUMERALS,
    DEFAULT_PUNCTUATE,
    DEFAULT_SMART_FORMAT,
    DOMAIN,
    INTEGRATION_NAME,
    MODELS,
)
from .util import api_key_fingerprint

_LOGGER = logging.getLogger(__name__)


def _api_key_selector() -> TextSelector:
    """Return a password-style API-key field."""
    return TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _model_selector() -> SelectSelector:
    """Return the Deepgram model selector."""
    labels = {
        "nova-3": "Nova-3 (recommended)",
        "nova-2": "Nova-2 (fallback)",
    }
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=model, label=labels.get(model, model))
                for model in MODELS
            ],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


async def _async_validate_key(hass: HomeAssistant, api_key: str) -> str:
    """Validate and normalize an API key."""
    clean_key = api_key.strip()
    if not clean_key:
        raise DeepgramAuthError("Deepgram API key is empty")
    await async_validate_api_key(hass, clean_key)
    return clean_key


class DeepgramSTTConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deepgram STT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                api_key = await _async_validate_key(self.hass, user_input[CONF_API_KEY])
            except DeepgramAuthError:
                errors["base"] = "invalid_auth"
            except (DeepgramConnectionError, DeepgramRateLimitError):
                errors["base"] = "cannot_connect"
            except DeepgramAPIError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating the Deepgram key")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(api_key_fingerprint(api_key))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=INTEGRATION_NAME,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_MODEL: user_input[CONF_MODEL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): _api_key_selector(),
                    vol.Required(CONF_MODEL, default=DEFAULT_MODEL): _model_selector(),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start the reauthentication flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect and validate a replacement API key."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if entry is None:
            return self.async_abort(reason="reauth_failed")

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                api_key = await _async_validate_key(self.hass, user_input[CONF_API_KEY])
            except DeepgramAuthError:
                errors["base"] = "invalid_auth"
            except (DeepgramConnectionError, DeepgramRateLimitError):
                errors["base"] = "cannot_connect"
            except DeepgramAPIError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reauthentication")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_API_KEY: api_key},
                )
                self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): _api_key_selector()}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""
        return DeepgramSTTOptionsFlow()


class DeepgramSTTOptionsFlow(OptionsFlow):
    """Handle options for Deepgram STT."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Deepgram transcription options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODEL,
                        default=data.get(CONF_MODEL, DEFAULT_MODEL),
                    ): _model_selector(),
                    vol.Required(
                        CONF_SMART_FORMAT,
                        default=bool(data.get(CONF_SMART_FORMAT, DEFAULT_SMART_FORMAT)),
                    ): BooleanSelector(),
                    vol.Required(
                        CONF_PUNCTUATE,
                        default=bool(data.get(CONF_PUNCTUATE, DEFAULT_PUNCTUATE)),
                    ): BooleanSelector(),
                    vol.Required(
                        CONF_NUMERALS,
                        default=bool(data.get(CONF_NUMERALS, DEFAULT_NUMERALS)),
                    ): BooleanSelector(),
                }
            ),
        )
