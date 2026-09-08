# Reolink Web Console for Home Assistant

A local custom integration that uses the same token-based CGI API as the Reolink
camera web console for authentication and snapshots, while giving Home Assistant
the camera's native RTSP preview stream for full-quality live video and audio.

## Install with HACS

1. In HACS, open **Integrations**, select the three-dot menu, then **Custom
   repositories**.
2. Add `https://github.com/rsre/HAReolink` with the **Integration** category.
3. Install **Reolink Web Console** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **Reolink Web Console**.

## Manual install

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

## Versions

Releases use semantic versioning (`MAJOR.MINOR.PATCH`). The integration version in
`manifest.json` always matches the GitHub release tag without its leading `v`.
See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Development validation

```bash
python -m compileall custom_components/reolink_web
```
