"""Videolink Doorbell integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VideolinkAuthError, VideolinkClient, VideolinkConnectionError
from .const import DEFAULT_VERIFY_SSL, DOMAIN, PLATFORMS, CONF_VERIFY_SSL

type VideolinkConfigEntry = ConfigEntry[VideolinkClient]

_LOGGER = logging.getLogger(__name__)

CARD_URL = "/videolink_doorbell/videolink-doorbell-camera-card.js"
CARD_PATH = Path(__file__).parent / "frontend" / "videolink-doorbell-camera-card.js"
CARD_VERSION = "0.5.1"
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the bundled Lovelace card once when the integration loads."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), True)]
    )
    await _async_register_card(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Persist the bundled card as a Lovelace module when possible."""
    versioned_url = f"{CARD_URL}?v={CARD_VERSION}"
    lovelace = hass.data.get(LOVELACE_DATA)
    resources = getattr(lovelace, "resources", None)
    if resources is None:
        add_extra_js_url(hass, versioned_url)
        return

    try:
        await resources.async_get_info()
        existing = next(
            (
                item
                for item in resources.async_items()
                if item.get("url", "").split("?", 1)[0] == CARD_URL
            ),
            None,
        )
        resource = {"res_type": "module", "url": versioned_url}
        if existing is None:
            await resources.async_create_item(resource)
        elif existing.get("url") != versioned_url or existing.get("type", existing.get("res_type")) != "module":
            await resources.async_update_item(existing["id"], resource)
    except (AttributeError, KeyError, TypeError, ValueError):
        _LOGGER.warning("Could not persist the dashboard card resource; using the frontend module fallback")
        add_extra_js_url(hass, versioned_url)


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
