# Reolink Web Console for Home Assistant

A local custom integration that uses the same token-based CGI API as the Reolink
camera web console for authentication and snapshots, while giving Home Assistant
the camera's native RTSP preview stream for full-quality live video and audio.

## Install

1. Copy `custom_components/reolink_web` into the matching directory in your Home
   Assistant configuration folder.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for
   **Reolink Web Console**.
4. Enter the camera host and the credentials used by its web console.

For cameras with their factory/self-signed certificate, leave **Verify HTTPS
certificate** disabled. Select `main` for the console's Clear stream or `sub` for
Fluent. RTSP must be enabled in the camera's network/server settings.

The integration communicates locally with the camera. Credentials are stored in
Home Assistant's config entry and are never committed to this repository.

## Development validation

```bash
python -m compileall custom_components/reolink_web
```
