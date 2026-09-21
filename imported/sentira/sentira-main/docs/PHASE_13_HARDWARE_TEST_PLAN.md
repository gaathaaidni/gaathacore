# Phase 13 Hardware Test Plan

Physical hardware was not available during implementation. These tests are required before production claims are made.

1. Generic RTSP camera: install the connector on the same LAN, pair it, use an approved RTSP endpoint, verify authentication, and confirm a real OPTIONS/DESCRIBE response and stream packet path.
2. ONVIF camera: confirm WS-Discovery response, authenticate against the device service, enumerate media profiles, retrieve a stream URI, and verify one frame through the connector.
3. NVR: discover the recorder, authenticate, enumerate channels, verify selected channel streams individually, and confirm only successful channels become cameras.
4. DVR: repeat the recorder and channel test over the supported device protocol. Record unsupported behavior as unavailable rather than inferred.
5. Major vendor: test one real Hikvision, Dahua, Uniview, Axis, Hanwha, Bosch, CP Plus, TVT, Tiandy, or Reolink unit and document the exact model and adapter status.

For every test capture connector version, sanitized error code, latency, camera/recorder model, and whether Edge -> MediaMTX/stream-gateway -> FFmpeg -> AI Worker carried real packets. Never attach passwords, raw tokens, or credentialed URLs.

## Phase 13.4 Evidence Record

Complete one row per physical device. Use only `PASS`, `FAIL`, `PARTIAL`, or `NOT TESTED`; never infer a result from another model or from fixture tests.

| Device | Vendor | Model | Firmware | Type | ONVIF endpoint | Discovery | Device info | Profiles | Stream URI | RTSP | Media packets | Full verify |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | Camera/NVR/DVR | sanitized host/path only | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |

For each completed test, record the date, connector version, latency, sanitized error code, and cloud command ID. Do not record credentials, credentialed URLs, private video, or raw tokens. Fixture and mock results belong in automated test output and must not be entered as hardware results.

The required cloud command sequence is:

```text
DISCOVER_ONVIF
GET_ONVIF_DEVICE_INFORMATION
GET_ONVIF_MEDIA_PROFILES
GET_ONVIF_STREAM_URI (explicit profile token)
GET_ONVIF_STREAM_URI (no profile token)
TEST_RTSP
VERIFY_ONVIF_DEVICE
```

Hardware validation is incomplete until the edge connector is on the device LAN, the cloud command lifecycle reaches a terminal result, and real media evidence is collected where feasible. An RTSP `OPTIONS` response alone proves connectivity only, not usable video media.
