# GAATHACORE SENTIRA REAL CAMERA PIPELINE

**Phase:** 19  
**Status:** **YELLOW**  
**Scope:** Local/Codespace Sentira only

## Pipeline

The existing per-camera manager now supervises three FFmpeg outputs from the
same source URL:

```text
CameraStreamManager
  ├─ MJPEG pipe -> existing AI Worker frame POST
  ├─ stream-copy segments -> existing RollingBuffer
  └─ stream-copy RTSP -> MediaMTX sentira/<org>/<site>/<camera>
                         -> Phase-18 HTTP media authorization
                         -> HLS
```

This is a third FFmpeg process because the existing two processes have
independent output formats and the manager already owns a per-camera process
list and termination path. A tee redesign was not introduced.

## Trusted path

`media_path(organizationId, siteId, cameraId)` is called server-side from the
manager camera configuration. It validates all identifiers and creates
`sentira/<organizationId>/<siteId>/<cameraId>`. No browser or start request
provides organization or site values.

## Credential handling

Camera creation rejects embedded URL credentials and stores the optional
password encrypted. The internal gateway projection contains only the existing
credential-free `streamUrl`, organization ID, site ID, camera ID, and enabled
state. Phase 19 preserves that boundary. It does not decrypt or transport
camera passwords, and it does not put credentials in media URLs, HLS/WHEP,
frontend code, AI payloads, logs, or reports.

Therefore the physical-camera portion is limited to sources already supported
by the existing credential-free gateway contract. No unsafe credential change
was made.

## Controlled source evidence

A deterministic FFmpeg `testsrc2`/sine RTSP source was consumed by the actual
`CameraStreamManager`, not only by `fixture_publisher.py`. The manager's
observed process tree contained:

- JPEG extraction to `pipe:1`.
- Rolling MP4 segment extraction to `/tmp/sentira-buffer/camera-a`.
- RTSP publication to `rtsp://127.0.0.1:8554/sentira/org-a/site-a/camera-a`.

MediaMTX v1.21.1 reported the manager-produced path online with H.264 and
MPEG-4 Audio. Fifty-four rolling MP4 files were observed. The AI Worker target
remained the configured `AI_WORKER_URL/frames` destination.

## HLS and authorization evidence

Using a Phase-18 playback JWT:

- HLS parent playlist: **200**.
- HLS child playlist: **200**.
- fMP4 init resource: **200**, 686 bytes.
- Current fMP4 media segment: **200**, 111,542 bytes.
- Unauthenticated request: **401**.
- Expired token: **401**.
- Organization B token/path: **401**.
- Organization A token on Organization B path: **401**.

MediaMTX publication authorization returned HTTP 204 through the existing
`/media/auth` callback. No second playback authorization mechanism was added.

## Lifecycle

The third process is registered immediately after creation. All three processes
are inspected for exit and are terminated by the existing `_terminate_processes`
path. The disposable runtime observed manager reconnect warnings after
MediaMTX was stopped, and MediaMTX restarted with its HLS muxer and RTSP
listeners cleanly recreated.

The existing task cancellation and shutdown path was preserved. No live test
was performed for deletion, reassignment, or dynamic disabled-camera refresh.

## Results

### PASSED

- Controlled actual CameraStreamManager -> MediaMTX publication.
- Trusted server-side organization/site/camera path construction.
- Phase-18 authorized HLS parent, child, init, and media segment.
- Cross-tenant and wrong-path rejection.
- Existing AI JPEG process still starts and posts to the same AI Worker target.
- Existing rolling MP4 process still writes segments.
- FFmpeg child exit/reconnect behavior and MediaMTX unavailable observation.
- MediaMTX v1.21.1 config validation.
- Stream Gateway tests: **15 passed**.

### NOT VERIFIED

- **REAL CAMERA TEST:** NOT RUN - no physical or remote camera was available.
- Credentialed physical-camera publication.
- Second actual manager-produced tenant stream.
- Live disabled, deleted, or reassigned camera lifecycle.
- WHEP: NOT VERIFIED - deferred to a dedicated playback validation phase.
- Browser playback: NOT VERIFIED.
- API Jest/build checks: blocked because `jest` and the full Node dependency set
  are unavailable.

## Security concerns and limits

The publication token is passed as an RTSP query parameter and is therefore
visible in the local FFmpeg command line. This follows the existing local
MediaMTX publisher contract but is not a production-readiness claim. Camera
passwords are not part of this argument. The predictable media path remains an
identifier only; Phase-18 MediaMTX authorization is the access boundary.

## Final status

**YELLOW.** The controlled manager path and authorized HLS media are proven
locally while real-camera, WHEP, browser, and several lifecycle edge cases
remain unverified. No production infrastructure was touched. No credentials
were added. No commit or push was performed.
