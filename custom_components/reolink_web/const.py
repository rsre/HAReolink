"""Constants for the Reolink Web Console integration."""

from homeassistant.const import Platform

DOMAIN = "reolink_web"

CONF_CHANNEL = "channel"
CONF_STREAM = "stream"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_CHANNEL = 0
DEFAULT_STREAM = "main"
DEFAULT_VERIFY_SSL = False

STREAM_MAIN = "main"
STREAM_SUB = "sub"
STREAMS = (STREAM_MAIN, STREAM_SUB)

PLATFORMS = [Platform.CAMERA]
