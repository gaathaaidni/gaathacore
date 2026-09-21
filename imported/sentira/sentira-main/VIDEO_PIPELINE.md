# Sentira AI Video Pipeline

Phase 6 uses the existing Stream Gateway as the secure video boundary. RTSP camera credentials stay server-side, streams are adapted to WebRTC where available, and HLS remains an optional fallback. Evidence records are event-linked and tenant-scoped with storage keys under `{organizationId}/{cameraId}/{eventId}`.

Phase 10G verified real snapshot bytes through MinIO-compatible storage and an
authorized API download. Video clip orchestration remains unimplemented.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C rolling-buffer limitations

The gateway can select rolling segments overlapping an event interval and concatenate
them with FFmpeg. Clip timing is constrained by source segment/keyframe boundaries;
no clip is represented when no source segment is available.

## Phase 10E evidence verification

Rolling-buffer segment selection still returns no clip when no real source segment
exists. MP4 generation, assembly, and API-to-gateway clip orchestration were not
runtime verified in Phase 10E because the Compose environment could not run. See
`PHASE_10E_COMPLETION_REPORT.md`.
