# Reolink Web Console for Home Assistant

A local custom integration that uses the same token-based CGI API as the Reolink
camera web console for authentication, snapshots, and the native authenticated
FLV live stream used by the browser player. A secondary RTSP producer supplies
the go2rtc audio backchannel for supported cameras.

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
Fluent. RTSP must be enabled for two-way audio, but video continues to use FLV.

## Two-way audio

Home Assistant's built-in go2rtc integration combines the FLV video producer with
an RTSP audio-backchannel producer. Open the camera through a WebRTC-capable card
and grant the browser microphone permission. Two-way audio depends on the camera
firmware exposing a compatible RTSP/ONVIF backchannel; unsupported models continue
to provide video and camera-to-browser audio normally.

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
