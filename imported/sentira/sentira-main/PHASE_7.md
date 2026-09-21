# Sentira AI Phase 7

Phase 7 implements production-oriented AI intelligence, real CCTV reliability controls, and enterprise operations foundations.

Implemented in this repository:
- AI Worker model-provider abstraction for detection, classification, segmentation, pose, tracking, and custom adapters.
- Lightweight object tracking with stable `trackId` values across normal frame movement.
- Rule engine support for duration, count, zone, line crossing, absence/presence, and sequence primitives; Phase 7 documents relationship, restricted-area, crowd, schedule, and repeated-activity patterns as generic rule definitions.
- Camera health classification, reconnect supervision, one task per camera, graceful cleanup, FPS heartbeat, stale-frame classification, and exponential backoff hooks in Stream Gateway.
- AI backpressure configuration strategy (`AI_FPS`, queue limits, frame skipping, newest-frame preference) documented for horizontal workers.
- Evidence SHA-256 integrity metadata with media size, duration, resolution, frame rate, camera, and event identifiers.
- Event alert suppression/cooldown and notification limiting primitives.
- Enterprise docs for analytics, reporting, privacy, retention, production security, RBAC, audit, observability, scaling, load testing, and disaster recovery.

Not claimed as physically verified: real RTSP cameras, live MinIO/RabbitMQ/Redis production integrations, and 100/500-camera capacity.
