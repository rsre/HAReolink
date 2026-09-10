"""Compatibility adapter for go2rtc composite stream registration."""

from __future__ import annotations

from typing import Any, Protocol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


class Go2RtcStreamsApi(Protocol):
    """Subset of the go2rtc client used by this integration."""

    async def list(self) -> dict[str, Any]:
        """List configured streams."""

    async def add(self, name: str, sources: list[str]) -> None:
        """Add or replace a stream."""


def get_streams_api(hass: HomeAssistant) -> Go2RtcStreamsApi | None:
    """Return a compatible streams API from the loaded go2rtc provider.

    Home Assistant does not currently expose public multi-producer camera stream
    registration. Keep the private-provider compatibility boundary isolated here.
    """
    for entry in hass.config_entries.async_entries("go2rtc"):
        if entry.state is not ConfigEntryState.LOADED:
            continue
        rest_client = getattr(entry.runtime_data, "_rest_client", None)
        streams = getattr(rest_client, "streams", None)
        if callable(getattr(streams, "list", None)) and callable(
            getattr(streams, "add", None)
        ):
            return streams
    return None
