# GAATHACORE PHASE 19 REPORT

**Date:** 2026-09-22  
**Scope:** Sentira only  
**Final status:** **YELLOW**

## Result

A controlled synthetic RTSP source exercised the actual `CameraStreamManager`.
The manager started three supervised FFmpeg children for one camera:

```text
synthetic RTSP source
  -> AI JPEG extraction -> AI Worker destination
  -> rolling MP4 segments -> RollingBuffer
  -> RTSP publication -> MediaMTX sentira/org-a/site-a/camera-a
  -> Phase-18 /media/auth -> authorized HLS
```

The manager-produced stream was online in MediaMTX. Authorized HLS parent,
child, fMP4 init, and a real media segment were retrieved. Cross-tenant and
invalid authorization requests were rejected. No Core mapping, deployment,
production configuration, or production credential was used.

## Exact files changed

- `imported/sentira/sentira-main/apps/stream-gateway/camera_manager.py`
- `imported/sentira/sentira-main/apps/stream-gateway/config.py`
- `imported/sentira/sentira-main/apps/stream-gateway/fixture_publisher.py`
- `imported/sentira/sentira-main/apps/stream-gateway/main.py`
- `imported/sentira/sentira-main/apps/stream-gateway/tests/test_phase7_reliability.py`
- `imported/sentira/sentira-main/apps/stream-gateway/tests/test_stream_gateway.py`
- `imported/sentira/sentira-main/docker-compose.yml`
- `GAATHACORE_PHASE_19_REPORT.md`
- `GAATHACORE_SENTIRA_REAL_CAMERA_PIPELINE.md`

No other product was modified. No commit or push was performed.

## Existing architecture

`CameraStreamManager` discovers enabled cameras through the protected internal
API projection and runs one supervision task per camera. Before this phase it
started two FFmpeg processes: MJPEG/JPEG extraction for the AI Worker and
stream-copy segment output for `RollingBuffer`. Termination and reconnect are
managed in the task `finally` block with exponential backoff.

## New publication architecture

A third FFmpeg process reads the same credential-free `streamUrl`, copies the
source tracks, and publishes to the RTSP endpoint configured by
`MEDIAMTX_RTSP_URL`. The path is constructed only by `media_path()` from the
cached Sentira `organizationId`, `siteId`, and camera `id`:

```text
sentira/<organizationId>/<siteId>/<cameraId>
```

The new process is added immediately to the existing per-camera process list.
All three children are checked for exit and are terminated by the existing
cleanup path. Partial startup is also covered: each successfully created child
is registered before the next child is created.

The existing Phase-18 MediaMTX HTTP callback remains the only media
authorization boundary. Publication uses the existing local publication token
setting; playback continues to use the Phase-18 scoped JWT callback.

## Credentials and security

The API stores camera passwords encrypted with AES-256-GCM and does not include
credentials in the gateway camera projection. Phase 19 does not add a decrypted
credential transport and does not weaken SSRF protections. Camera credentials
are not placed in browser, HLS, WHEP, AI Worker payloads, logs, or reports.

The local publication token is passed as an RTSP query parameter because that is
the existing MediaMTX publication contract. It is a service token, not a camera
password, and remains visible to the local FFmpeg process arguments. This is a
known local operational concern and is not claimed as production readiness.

## Validation evidence

### PASSED

- Focused and full Stream Gateway tests: **15 passed, 0 failed**.
- Python compilation and `compileall`: **passed**.
- MediaMTX v1.21.1 configuration validation: **passed**.
- Local Compose interpolation with disposable placeholder values: **passed**.
- Actual manager process tree: three FFmpeg children were observed:
  - JPEG output: `pipe:1`, `fps=2`.
  - Rolling MP4 output: `segment-%Y%m%dT%H%M%S.mp4`.
  - MediaMTX output: `rtsp://127.0.0.1:8554/sentira/org-a/site-a/camera-a`.
- MediaMTX callback publication decision: HTTP **204**.
- Manager-produced MediaMTX path: online with H.264 and MPEG-4 Audio tracks.
- Authorized HLS parent: **200**.
- Authorized HLS child: **200**.
- Authorized HLS init resource: **200**, 686 bytes.
- Authorized HLS media segment: **200**, 111,542 bytes.
- RollingBuffer: **54** MP4 segment files observed during the run.
- AI Worker destination/configuration: unchanged; the controlled AI sink received
  the manager's frame POSTs and no camera credentials were sent.
- Unauthenticated HLS final response: **401**.
- Expired-token HLS final response: **401**.
- Organization B token/path against the controlled A runtime: **401**.
- Organization A token against the B path: **401**.
- MediaMTX stop: existing publication/HLS sessions terminated and manager logged
  FFmpeg exit with reconnect backoff.
- MediaMTX restart: service restarted successfully; manager supervision remained
  active and retried publication.
- `git diff --check`: **passed**.

### NOT VERIFIED

- **REAL CAMERA TEST:** NOT RUN - no physical or remote camera was available.
- Organization B actual manager-produced stream: NOT RUN; the controlled runtime
  had one synthetic camera.
- Disabled Camera A and reassigned Camera A against a live manager-produced
  stream: not run in the disposable runtime. Phase-18 callback unit/runtime
  evidence covers fresh state rejection, and existing focused tests cover the
  disabled case.
- Camera deletion/unassignment live lifecycle: not run.
- Application shutdown orphan check beyond container/process cleanup: not run as
  a separate production-like deployment test.
- WHEP: NOT VERIFIED - deferred to a dedicated playback validation phase.
- Browser playback: NOT VERIFIED. The existing `/media-test` page was not used
  as proof.
- Physical-camera credentialed publication: not verified. The current gateway
  contract intentionally excludes username/password.

### BLOCKED / UNAVAILABLE

- Sentira API Jest tests were not executable because `jest` is not installed in
  the workspace (`sh: jest: not found`).
- Full API and frontend TypeScript builds were not run because their dependency
  installations are unavailable in this workspace.

## Process lifecycle

Start, source failure, FFmpeg exit, reconnect backoff, MediaMTX unavailable,
and MediaMTX restart were exercised. The new child is included in the existing
termination list. Disabled/deleted camera state is still dependent on the
existing camera configuration refresh/lifecycle behavior and was not redesigned.

## Final assessment

**YELLOW.** The actual CameraStreamManager controlled publication path and
Phase-18 authorized HLS media are proven locally, while AI JPEG and rolling MP4
outputs remain functional. Real physical camera operation, WHEP, browser
playback, second-tenant manager output, several lifecycle edge cases, and API
Jest/build validation remain unverified. This phase does not claim production
readiness.

Do not proceed to Core/Sentira organization mapping from this phase. Stop for
review.
