# GaathaCore Sentira Media Pipeline Implementation

Date: 2026-09-22
Scope: Sentira only
Status: CONTROLLED LOCAL PIPELINE PROVEN; REAL CAMERA AND AUTHORIZED PLAYBACK NOT IMPLEMENTED

## 1. Existing architecture

`CameraStreamManager` discovers enabled cameras through the protected internal
API route. For each camera it starts one FFmpeg process that extracts JPEG frames
for the AI worker and a second FFmpeg process that writes rolling MP4 segments.
`RollingBuffer` owns retention and clip assembly. There is no existing FFmpeg
output aimed at MediaMTX.

`fixture_publisher.py` is a separate deterministic FFmpeg publisher. The Next.js
application has no existing HLS or WHEP consumer. The API issues short-lived
playback JWTs and the gateway validates them for metadata/control routes, but no
MediaMTX request consumes those JWTs.

## 2. Architecture selected for local proof

The smallest safe proof keeps the real camera manager unchanged:

```text
fixture_publisher.py
  -> RTSP publish
  -> MediaMTX v1.21.1
  -> HLS parent/session URLs
  -> local /media-test probe page
```

The fixture now defaults to a server-generated path:

```text
sentira/<organization-id>/<site-id>/<camera-id>
```

The path is an identifier, not an authorization mechanism. The IDs are supplied
by the controlled fixture command here and must be selected by trusted Sentira
server state for any future camera publisher.

## 3. Why this matches the repository

The repository already contains the fixture, the FFmpeg dependency, and the
MediaMTX Compose service. It does not contain a MediaMTX auth callback, JWT/JWKS
configuration, signed URL mechanism, or proxy. Adding a third FFmpeg output to
the real camera manager before resolving that boundary would publish an
unauthorized direct path and would require assumptions about credential handling.

## 4. Exact files changed

- `imported/sentira/sentira-main/apps/stream-gateway/media_paths.py`
- `imported/sentira/sentira-main/apps/stream-gateway/fixture_publisher.py`
- `imported/sentira/sentira-main/apps/stream-gateway/tests/test_fixture_and_buffer.py`
- `imported/sentira/sentira-main/docker-compose.yml`
- `imported/sentira/sentira-main/apps/web/src/app/media-test/page.tsx`
- `GAATHACORE_PHASE_17_REPORT.md`
- `GAATHACORE_SENTIRA_MEDIA_PIPELINE_IMPLEMENTATION.md`

No real camera process, API, production Compose, Core, Suite, POS, PostPilot,
database, DNS, Nginx, or credential code was changed.

## 5. Exact media flow

The fixture generates `testsrc2` video and a sine-wave audio track, encodes H.264
and AAC, and publishes over TCP to:

```text
rtsp://127.0.0.1:8554/sentira/org-a/site-a/camera-a
```

MediaMTX receives that RTSP publisher and creates HLS at:

```text
http://127.0.0.1:8888/sentira/org-a/site-a/camera-a/index.m3u8
```

The local Compose file now exposes HLS port `8888` in addition to RTSP `8554`
and WebRTC HTTP `8889`. Production Compose remains internal-only.

## 6. FFmpeg behavior and supervision

The fixture command is deterministic and disposable. Its publisher identity is
the trusted path tuple `org-a/site-a/camera-a`; it exposes no camera credentials.
The existing real-camera FFmpeg processes remain supervised by
`CameraStreamManager`, with reconnect and termination behavior unchanged.

The controlled fixture process is supervised by its disposable container for
this phase. A future real-camera MediaMTX output must be added to the existing
per-camera process list and terminated by `_terminate_processes`; that change
was intentionally not made because actual media authorization is absent.

## 7. MediaMTX path behavior

`media_path()` accepts only non-empty URL-safe trusted identifiers and rejects
path fragments containing `/`. Tests prove that changing organization or site
changes the resulting path. UUID obscurity is not treated as authorization.

## 8. HLS result

The disposable MediaMTX run logged the path online and created an HLS muxer for
the path. The parent playlist returned HTTP 200 and `#EXTM3U`. MediaMTX uses a
cookie-check redirect and session query parameters for child/segment retrieval;
unqualified child requests returned HTTP 401. A child request with the proper
session query returned HTTP 200 in the session probe. Segment retrieval is
session-dependent and was not treated as a successful authorization test.

## 9. WHEP result

The WHEP route exists. An empty SDP POST returned HTTP 400, which is not a valid
WebRTC negotiation. A valid browser SDP offer was not generated, so WHEP is NOT
VERIFIED.

## 10. Frontend result

`/media-test` is a deliberately small local probe page. It points directly at
the controlled HLS fixture, displays media element state, and explicitly says it
is not an authorization boundary. It does not call the playback authorization
API and does not claim authorized playback. The page is a consumer surface, not
browser playback proof; no browser media client was run.

## 11. Camera credential handling

No camera credentials were exposed, copied, decrypted, or added to the fixture.
The real gateway receives internal camera data, but the phase did not establish
that the current `streamUrl` contract safely supplies authenticated camera
credentials to a new MediaMTX output. That is a separate blocker.

## 12. Two-organization result

Source/path tests pass for two organization values and reject path fragments.
They prove deterministic path binding only:

```text
org-a/site-a/camera-a != org-b/site-a/camera-a
```

Actual media authorization isolation is BLOCKED because MediaMTX is not
connected to Sentira authorization. Frontend hiding and UUID randomness are not
used as isolation evidence.

## 13. Authorization boundary status

The intended boundary remains:

```text
Sentira JWT
  -> API camera/org/site authorization
  -> playback authorization JWT
  -> MEDIA AUTHORIZATION BOUNDARY (MISSING)
  -> MediaMTX
  -> HLS/WHEP
```

The missing boundary must be implemented as a reviewed MediaMTX auth callback,
MediaMTX JWT/JWKS configuration, or server-side media proxy before secure
browser playback can be claimed.

## 14. Security findings

Implemented: trusted path construction, path-fragment rejection, local HLS
exposure for development, no credential exposure in the fixture, existing API
and gateway metadata JWT validation.

Unimplemented: MediaMTX authorization, path-level tenant authorization, token
replay prevention, active-session revocation, disabled-camera revocation at the
media layer, and real-camera RTSP-to-MediaMTX publication.

Unverified: browser playback, valid WHEP negotiation, two-organization media
rejection, stale-camera behavior, and direct MediaMTX access behavior under a
Sentira token.

Blocked: safe real-camera publication until the credential contract and media
authorization boundary are explicitly designed.

## 15. Exact commands

```text
cd imported/sentira/sentira-main/apps/stream-gateway
PYTHONPATH=. pytest -q tests/test_fixture_and_buffer.py
python -m compileall -q media_paths.py fixture_publisher.py camera_manager.py main.py
PYTHONPATH=. pytest -q tests/test_stream_gateway.py tests/test_fixture_and_buffer.py tests/test_phase7_reliability.py

cd imported/sentira/sentira-main
npm --workspace apps/web run build

docker build -t phase17-sentira-stream-gateway apps/stream-gateway
docker run --rm --name phase17-sentira-mediamtx -p 8554:8554 -p 8888:8888 -p 8889:8889 bluenviron/mediamtx:latest
docker run --rm --network host phase17-sentira-stream-gateway python fixture_publisher.py --host 127.0.0.1 --organization-id org-a --site-id site-a --camera-id camera-a
```

The runtime containers were disposable and removed after probing.

## 16. Exact test results

PASSED: focused fixture/path tests, `4 passed`.

PASSED: gateway focused suite, `11 passed`.

PASSED: Python compile.

PASSED: frontend production build. Existing unrelated `<img>` lint warnings
remain.

PASSED: MediaMTX v1.21.1 startup and RTSP path publication. Logs showed H.264
and MPEG-4 Audio tracks online at the server-generated path.

PASSED: HLS parent response, HTTP 200 with `#EXTM3U`.

PARTIAL: HLS child/session behavior. Session-qualified child retrieval returned
HTTP 200; unqualified child/segment requests returned HTTP 401. A stable
end-to-end segment replay was not used as authorization evidence.

NOT VERIFIED: valid WHEP SDP negotiation.

NOT RUN: browser playback, physical camera publication, full Compose stack, and
live two-organization API/media integration.

## 17. Remaining blockers

The real camera manager does not publish to MediaMTX. The API-issued playback
JWT does not reach an actual HLS/WHEP request. MediaMTX direct access is not
tenant-authorized. Browser playback and valid WHEP are unverified.

## 18. Is real camera support technically possible?

The FFmpeg mechanism is technically capable of a third output, and the
MediaMTX path contract is now defined. Safe real-camera support is not yet
implemented because source credential handling and the authorization boundary
are unresolved. This phase does not force that change.

## 19. Is browser playback working?

No. The local `/media-test` consumer is implemented and the HLS parent is
available, but no browser/media client successfully consumed the stream during
this phase.

## 20. Is playback authorization enforced?

No. API and gateway metadata authorization exist; the actual MediaMTX media
request is not protected by the Sentira playback result.

Core mapping remains blocked.