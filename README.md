# Videolink Doorbell for Home Assistant

A local custom integration that uses the token-based CGI API and the native authenticated
FLV live stream. A secondary RTSP producer supplies the go2rtc audio backchannel for supported cameras.

## Install with HACS

1. In HACS, open **Integrations**, select the three-dot menu, then **Custom
   repositories**.
2. Add `https://github.com/rsre/VideolinkDoorbell` with the **Integration** category.
3. Install **Videolink Doorbell** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **Videolink Doorbell**.

## Manual install

1. Copy `custom_components/videolink_doorbell` into the matching directory in your Home
   Assistant configuration folder.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for
   **Videolink Doorbell**.
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

The integration bundles and automatically registers the **Videolink Doorbell Camera**
dashboard card. Add it through the dashboard card picker, or use YAML:

```yaml
type: custom:videolink-doorbell-camera-card
entity: camera.your_videolink_camera
title: Front door
hide_title: false
disable_popup: false
debug: false
```

Hold **Hold to talk** while speaking and release it to stop. The card requests
microphone access only when the control is pressed and releases the microphone
immediately afterward. Home Assistant must be opened over HTTPS (or localhost)
because browsers block microphone capture on insecure origins.

Click the video to open Home Assistant's native camera dialog, or set
`disable_popup` to `true` to disable that behavior. Set `hide_title` to `true` for
a titleless card. The stream starts muted; using push-to-talk keeps
inbound sound muted while transmitting to avoid feedback, then enables it on
release so the reply can be heard.

For an audio-only intercom without a video stream, use the bundled **Videolink
Doorbell Audio** card from the card picker, or add it in YAML:

```yaml
type: custom:videolink-doorbell-audio-card
entity: camera.your_videolink_camera
title: Front door intercom
hide_title: false
debug: false
```

The audio card negotiates only camera audio and the push-to-talk backchannel. It
uses the same speaker mute control, HTTPS check, and automatic listening after
push-to-talk as the camera card.

Set `debug: true` on either card to display live WebRTC transport and PTT timing
diagnostics. The panel reports connection time, RTT, inbound jitter and jitter
buffering, packet counters, codec, microphone permission time, track attachment,
and the delay until the first outbound microphone packet. Use **Copy diagnostics**
to copy the complete report.

The integration communicates locally with the camera. Credentials are stored in
Home Assistant's config entry and are never committed to this repository.

## Versions

Releases use semantic versioning (`MAJOR.MINOR.PATCH`). The integration version in
`manifest.json` always matches the GitHub release tag without its leading `v`.
See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Development validation

```bash
python -m compileall custom_components/videolink_doorbell
```
