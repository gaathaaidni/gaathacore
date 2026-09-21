# Sentira AI — Phase 10C Implementation Plan

## Audit findings

The Phase 10B runtime topology, deterministic AI ingress, Redis rule-state
adapter, and FFmpeg rolling-segment foundation are present. Direct source audit
confirmed the remaining disconnected pieces are the API-side AMQP consumer,
storage transfer/authorization layer, detection-to-rule/event orchestration,
event evidence persistence, deterministic RTSP fixture, and dependency probes.
The existing `EventMedia` model also lacks persisted integrity fields, requiring
a reversible migration rather than schema synchronization.

## Implementation sequence

1. Add validated detection-envelope contracts and an API RabbitMQ consumer with
   durable topology, manual acknowledgements, bounded retry/DLQ routing, tenant
   camera verification, and correlation-aware structured logging.
2. Add detection orchestration that evaluates organization/camera-scoped rules,
   creates real events, broadcasts them to the organization room, and schedules
   snapshot evidence without falsely marking failed evidence ready.
3. Add an S3-compatible MinIO storage abstraction, integrity-aware `EventMedia`
   persistence and authorized event-media download endpoint; add a reversible
   integrity migration.
4. Extend the gateway rolling-buffer utilities with interval selection and clip
   assembly, plus a deterministic FFmpeg/MediaMTX fixture publisher.
5. Add focused unit/integration-foundation tests for envelopes, retries,
   evidence authorization/integrity, tenant scopes, and fixture/buffer failure
   behavior; upgrade health results to runtime probes with UP/DOWN/UNKNOWN.
6. Update only relevant operational documentation and create a completion report
   that separates implemented code from runtime verification.
