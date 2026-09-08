"""Config flow for Reolink Web Console."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .api import ReolinkAuthError, ReolinkClient, ReolinkConnectionError, ReolinkError
from .const import (
    CONF_CHANNEL,
    CONF_RTSP_PORT,
    CONF_STREAM,
    CONF_VERIFY_SSL,
    DEFAULT_CHANNEL,
    DEFAULT_RTSP_PORT,
    DEFAULT_STREAM,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    STREAMS,
)


class ReolinkWebConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup through the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Collect and validate camera settings."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = ReolinkClient(
                async_get_clientsession(self.hass),
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                port=user_input[CONF_PORT],
                verify_ssl=user_input[CONF_VERIFY_SSL],
            )
            try:
                info = await client.device_info()
            except ReolinkAuthError:
                errors["base"] = "invalid_auth"
            except ReolinkConnectionError:
                errors["base"] = "cannot_connect"
            except ReolinkError:
                errors["base"] = "unknown"
            else:
                unique_id = info.serial or f"{client.host}:{client.port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info.name, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.1.123"): str,
                vol.Required(CONF_PORT, default=443): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CHANNEL, default=DEFAULT_CHANNEL): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Required(CONF_STREAM, default=DEFAULT_STREAM): SelectSelector(
                    SelectSelectorConfig(options=list(STREAMS), translation_key="stream")
                ),
                vol.Required(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
