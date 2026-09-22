# Sentira Multi-Tenant Media Validation

## Validation target

The existing `CameraStreamManager` now reconciles the protected camera projection and uses the existing per-camera process list for AI JPEG extraction, RollingBuffer segments, and RTSP publication. Media paths remain derived from trusted `organizationId`, `siteId`, and camera ID values.

## Automated evidence

The focused Stream Gateway suite completed with **19 passed, 0 failed**.

Covered behavior:

- A and B publication paths are distinct.
- A token/path and B token/path are each accepted by the callback contract.
- Cross-tenant path/token combinations are rejected.
- Missing and expired tokens are rejected.
- Changed organization/site claims are rejected.
- A stale token is rejected after the current camera mapping changes.
- Disabled and deleted camera projections stop manager streams.
- All three manager child processes are cleaned up.
- Camera passwords do not appear in publication command arguments.

## Runtime limitation

This workspace does not contain `ffmpeg` or `mediamtx`, so Phase 20 did not produce live two-manager MediaMTX evidence. No HTTP 200/401/403 results from a running MediaMTX instance are claimed here. Phase 19 remains the source of the previously recorded single-manager live HLS evidence.

## Browser probe

The existing `/media-test` page now accepts a token for each of the two controlled paths and performs an HLS parent request with an `Authorization: Bearer` header. This proves the HTTP response when run against the local stack. Native `<video>` playback was not claimed because the page cannot attach bearer headers without an HLS player library, and no browser runtime was available in this container.

## WHEP

WHEP was not verified in Phase 20. No custom WebRTC implementation was added.

## Credential handling

The stream manager consumes the internal camera projection, which excludes camera username/password fields. The publication token remains a local service token in the RTSP query argument and is visible to local FFmpeg process inspection. This is documented as production hardening rather than redesigned in this phase.
