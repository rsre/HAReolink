"""Videolink Doorbell integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VideolinkAuthError, VideolinkClient, VideolinkConnectionError
from .const import DEFAULT_VERIFY_SSL, DOMAIN, PLATFORMS, CONF_VERIFY_SSL

type VideolinkConfigEntry = ConfigEntry[VideolinkClient]

CARD_URL = "/videolink_doorbell/videolink-doorbell.js"
CARD_PATH = Path(__file__).parent / "frontend" / "videolink-doorbell-camera-card.js"
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the bundled Lovelace card once when the integration loads."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v=0.11.0")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VideolinkConfigEntry) -> bool:
    """Set up Videolink Doorbell from a config entry."""
    client = VideolinkClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        port=entry.data[CONF_PORT],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    try:
        await client.ensure_login()
    except VideolinkAuthError as err:
        raise ConfigEntryAuthFailed from err
    except VideolinkConnectionError as err:
        raise ConfigEntryNotReady from err
    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VideolinkConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
