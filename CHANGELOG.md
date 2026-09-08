# Changelog

All notable changes are documented here. This project follows Semantic Versioning.

## [0.4.0] - 2026-09-08

### Added

- Added visual-editor and YAML settings to hide the card title and request unmuted
  playback on load.
- Clicking the video now opens Home Assistant's native camera more-info dialog.

### Removed

- Removed the card's dedicated fullscreen button.

## [0.3.2] - 2026-09-08

### Changed

- Temporarily mute inbound camera audio while push-to-talk is active to prevent
  feedback, then restore the speaker's previous mute state on release.

## [0.3.1] - 2026-09-08

### Fixed

- Register the complete Reolink RTSP producer so go2rtc can discover and negotiate
  its ONVIF `sendonly` PCMU backchannel track. The previous audio-only media filter
  could omit the camera-speaker backchannel.

## [0.3.0] - 2026-09-08

### Added

- Bundled Reolink Web Camera Lovelace card with native Home Assistant WebRTC
  signaling, hold-to-talk microphone control, speaker mute, and fullscreen.
- Automatic frontend module registration; no separate card repository or dashboard
  resource installation is required.

## [0.2.0] - 2026-09-08

### Added

- Added a secondary RTSP audio producer with go2rtc backchannel support while
  retaining the authenticated web-console FLV stream as the primary video source.

## [0.1.1] - 2026-09-08

### Fixed

- Fixed config-flow loading by defining the integration's channel key locally.
- Replaced RTSP playback with the authenticated FLV endpoint used by the camera's
  original web console.

## [0.1.0] - 2026-09-08

### Added

- Home Assistant UI configuration flow.
- Reolink web-console CGI authentication and automatic token renewal.
- Authenticated JPEG camera snapshots.
- Native main and sub RTSP live streams with audio support.
- Configurable channel, HTTPS port, RTSP port, and TLS verification.
- HACS metadata and automated HACS/Hassfest validation.

[0.4.0]: https://github.com/rsre/HAReolink/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/rsre/HAReolink/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/rsre/HAReolink/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/rsre/HAReolink/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/rsre/HAReolink/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/rsre/HAReolink/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/rsre/HAReolink/releases/tag/v0.1.0
