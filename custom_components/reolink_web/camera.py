"""Camera platform for Reolink Web Console."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CHANNEL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo as HADeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DeviceInfo, ReolinkClient
from .const import CONF_RTSP_PORT, CONF_STREAM, DEFAULT_CHANNEL, DEFAULT_RTSP_PORT, DEFAULT_STREAM, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[ReolinkClient],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the camera entity."""
    client = entry.runtime_data
    info = await client.device_info()
    async_add_entities([ReolinkWebCamera(entry, client, info)])


class ReolinkWebCamera(Camera):
    """A Reolink camera using the web console API and native preview stream."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, entry: ConfigEntry[ReolinkClient], client: ReolinkClient, info: DeviceInfo) -> None:
        super().__init__()
        self._entry = entry
        self._client = client
        self._channel = entry.data.get(CONF_CHANNEL, DEFAULT_CHANNEL)
        self._stream = entry.data.get(CONF_STREAM, DEFAULT_STREAM)
        self._rtsp_port = entry.data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT)
        identifier = info.serial or f"{client.host}:{client.port}"
        self._attr_unique_id = f"{identifier}_channel_{self._channel}"
        self._attr_device_info = HADeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=info.name,
            manufacturer="Reolink",
            model=info.model,
            sw_version=info.firmware,
            configuration_url=client.base_url,
        )

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Return the current console snapshot."""
        return await self._client.snapshot(self._channel)

    async def stream_source(self) -> str:
        """Return the native preview source for Home Assistant's stream worker."""
        return self._client.rtsp_url(self._channel, self._stream, self._rtsp_port)
