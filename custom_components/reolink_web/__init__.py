"""Reolink Web Console integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ReolinkAuthError, ReolinkClient, ReolinkConnectionError
from .const import DEFAULT_VERIFY_SSL, DOMAIN, PLATFORMS, CONF_VERIFY_SSL

type ReolinkConfigEntry = ConfigEntry[ReolinkClient]


async def async_setup_entry(hass: HomeAssistant, entry: ReolinkConfigEntry) -> bool:
    """Set up Reolink Web Console from a config entry."""
    client = ReolinkClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        port=entry.data[CONF_PORT],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    try:
        await client.ensure_login()
    except ReolinkAuthError as err:
        raise ConfigEntryAuthFailed from err
    except ReolinkConnectionError as err:
        raise ConfigEntryNotReady from err
    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ReolinkConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
