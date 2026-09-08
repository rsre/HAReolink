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

The integration bundles and automatically registers the **Reolink Web Camera**
dashboard card. Add it through the dashboard card picker, or use YAML:

```yaml
type: custom:reolink-web-camera-card
entity: camera.your_reolink_camera
title: Front door
hide_title: false
```

Hold **Hold to talk** while speaking and release it to stop. The card requests
microphone access only when the control is pressed and releases the microphone
immediately afterward. Home Assistant must be opened over HTTPS (or localhost)
because browsers block microphone capture on insecure origins.

When the browser reports an insecure context, the card displays an HTTPS warning
and disables push-to-talk. Browser-recognized secure localhost addresses continue
to work without a certificate.

Click the video to open Home Assistant's native camera dialog. Set `hide_title` to
`true` for a titleless card. The stream starts muted; using push-to-talk keeps
inbound sound muted while transmitting to avoid feedback, then enables it on
release so the reply can be heard.

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
