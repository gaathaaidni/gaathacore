# GAATHACORE PHASE 17 REPORT

Date: 2026-09-22
Scope: Sentira only
Status: CONTROLLED LOCAL MEDIA PIPELINE PROVEN; AUTHORIZED PLAYBACK BLOCKED

## Executive result

Phase 17 established the smallest controlled local path:

```text
synthetic FFmpeg fixture
  -> RTSP
  -> MediaMTX v1.21.1
  -> HLS parent and session endpoints
  -> local Next.js media probe
```

The fixture now uses the server-generated path
`sentira/fixture-org/fixture-site/fixture-camera`. The path is tested as a
tenant/site/camera identifier and is not treated as authorization.

The real Sentira camera path remains unimplemented. The API playback JWT still
does not reach MediaMTX. Browser playback and valid WHEP negotiation are not
verified. Core mapping remains blocked.

## Architecture and changes

The existing `CameraStreamManager` still has two FFmpeg outputs per camera:
AI JPEG extraction and rolling MP4 segments. It has no MediaMTX output. The
existing fixture was the correct controlled source because it already exercises
FFmpeg RTSP publication without a physical camera or camera credentials.

Added:

- Trusted `media_path()` construction from organization, site, and camera IDs.
- Fixture CLI options for those IDs, with the deterministic path as default.
- Source/path tests covering organization isolation at the configuration level.
- Local HLS port `8888` exposure in development Compose.
- Minimal `/media-test` HLS probe page.

The production Compose file was not changed and remains internal-only for
MediaMTX. No production, Core, Suite, POS, PostPilot, DNS, Nginx, or database
work was performed.

## Verification

PASSED:

- Stream Gateway focused tests: `11 passed`.
- Fixture/path tests: `4 passed`.
- Python compilation.
- Next.js frontend build.
- Disposable MediaMTX v1.21.1 startup.
- RTSP fixture publication to the generated path; MediaMTX logged the path
  online with H.264 and MPEG-4 Audio tracks.
- HLS parent HTTP 200 with `#EXTM3U`.
- MediaMTX session behavior was observed: session-qualified child retrieval can
  return HTTP 200; unqualified child/segment requests return HTTP 401.
- Empty SDP WHEP control request returned HTTP 400.

NOT VERIFIED:

- Valid WHEP SDP negotiation.
- Browser playback.
- Stable end-to-end HLS segment consumption by a real browser/media client.
- Actual Sentira camera to gateway to MediaMTX publication.
- Actual two-organization media authorization isolation.

BLOCKED:

- Playback authorization at the MediaMTX request boundary.
- Safe real-camera publication until credential flow and media authorization are
  explicitly connected.
- Core mapping.

## Required boundary

```text
Sentira JWT
  -> API camera/org/site authorization
  -> playback authorization
  -> [MISSING MEDIA AUTHORIZATION BOUNDARY]
  -> MediaMTX
  -> HLS/WHEP
```

The local page intentionally consumes the controlled HLS URL directly and says
that it is not an authorization boundary. It must not be promoted as secure
playback.

## Security review

Implemented: path construction from trusted values, path fragment validation,
local-only HLS exposure, no fixture credential handling, and preservation of
existing AI JPEG and rolling-segment behavior.

Unimplemented: MediaMTX auth, signed media URLs or proxying, replay prevention,
active-session revocation, disabled-camera enforcement at MediaMTX, and direct
media access isolation.

Unverified: browser/WHEP behavior, path enumeration impact, stale gateway cache
behavior, and two-organization rejection at the media request.

## Exact commands

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

All disposable containers used for the runtime probe were removed. No commit or
push was performed.

## Stop condition

Phase 17 stops here. It does not start Sentira-to-Core mapping, claim production
readiness, claim secure browser playback, or claim playback authorization. The
next phase requires review of the MediaMTX authorization boundary and the real
camera credential contract.