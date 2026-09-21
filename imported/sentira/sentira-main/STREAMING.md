
## Phase 6 MediaMTX/WebRTC integration

Phase 10G verified MediaMTX health, deterministic fixture publishing, supervised
FFmpeg processes, and rolling-buffer segments in the running Compose stack.

The Stream Gateway remains the browser-safe boundary for live video. Camera RTSP usernames and passwords are decrypted only for internal services and are never returned to the web client. Browser clients request playback metadata through API-controlled routes and receive WebRTC/WHEP or HLS adapter URLs, not raw RTSP URLs.

Required variables: `STREAM_GATEWAY_URL`, `STREAM_GATEWAY_INTERNAL_TOKEN`, `MEDIAMTX_URL`, `WEBRTC_ENABLED`, `HLS_ENABLED`, `MAX_ACTIVE_STREAMS`.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C RTSP fixture

`rtsp-fixture` publishes FFmpeg's synthetic `testsrc2` stream to MediaMTX path
`fixture`; it does not require a physical camera or downloaded video.

## Phase 10E verification status

The synthetic RTSP fixture and gateway FFmpeg supervision remain unverified at
runtime because Docker/MediaMTX were unavailable. No FFmpeg extraction, reconnect,
or stream health success is claimed; see `PHASE_10E_COMPLETION_REPORT.md`.
