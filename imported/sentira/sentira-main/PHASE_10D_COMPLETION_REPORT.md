# Sentira AI — Phase 10D Completion Report

## Status: PARTIALLY VERIFIED — NOT PRODUCTION READY

This is a direct source and local-test audit of the Phase 10C implementation. It
does **not** start Phase 11 and does not treat source presence as runtime proof.

## IMPLEMENTED

- `apps/api/package.json` now declares the real production AMQP client
  `amqplib`. No fake broker client or in-memory AMQP fallback was introduced.
- The existing, single `DetectionConsumerService` is the ingress to the existing
  `DetectionProcessorService`. It declares a durable direct exchange, durable
  queue, routing key, durable DLX/DLQ, manual acknowledgements, prefetch,
  bounded retries, malformed-message dead-lettering, correlation propagation,
  reconnect scheduling, structured lifecycle logs, and orderly channel/connection
  shutdown.
- The source path remains detection → tenant/site/camera validation → rule engine
  → event → organization-scoped WebSocket broadcast. Snapshot attachment stores
  real decoded JPEG bytes through the S3-compatible storage service, with MIME
  type, byte count, SHA-256, metadata, and an `EventMedia` record.
- Authorized media reads query by media ID, event ID, **and** organization ID;
  an EventMedia ID alone cannot cross the tenant boundary.
- The Stream Gateway retains supervised FFmpeg JPEG extraction and segmented
  rolling buffers. Missing buffer segments return no clip rather than creating
  fake video.

## VERIFIED

- TypeScript lint/type checking completed after the consumer change.
- The package registry attempt was performed and recorded below. It returned 403;
  this is verification of an environment limitation, not a dependency fix.
- Docker was checked and is absent (`docker: command not found`).

## PARTIALLY VERIFIED

- Existing focused API unit tests cover detection-envelope rejection and the
  stream-gateway Python tests cover missing rolling segments. The consumer source
  compiles, but cannot make a broker connection until its declared dependency can
  be fetched into the lockfile/image.
- Redis state services use Redis when `REDIS_URL` is configured and throw on an
  unavailable configured server. The runtime Redis key/TTL/restart behavior has
  not been exercised.
- The custom S3-compatible storage implementation calculates SHA-256 and uses
  server-side credentials. MinIO bucket initialization, upload/download, timeout,
  and object-existence behavior have not been exercised against MinIO.
- Existing internal Stream Gateway endpoints require `X-Internal-Token`; the
  API-to-Gateway event clip-request endpoint and EventMedia clip persistence are
  still not implemented.

## BLOCKED BY ENVIRONMENT

- `npm install --workspace apps/api amqplib@^0.10.9` returned HTTP 403 from
  `https://registry.npmjs.org/amqplib`. Therefore `package-lock.json` cannot be
  truthfully updated, `npm ci` cannot install the new declaration, and the API
  Docker image cannot yet be rebuilt with AMQP. The dependency declaration is
  correct; the packaged dependency is **not verified**.
- Docker is unavailable. Compose config/build/up, PostgreSQL migrations,
  RabbitMQ delivery/ack/DLQ/reconnect, Redis restart, MinIO storage, MediaMTX RTSP,
  FFmpeg processes, AI Worker broker publishing, authenticated WebSocket traffic,
  and the full golden path were not run. **RUNTIME VERIFICATION BLOCKED — DOCKER
  UNAVAILABLE.**

## NOT IMPLEMENTED

- A live two-tenant HTTP/WebSocket E2E suite covering cameras, zones, rules,
  events, notifications, analytics, audit logs, EventMedia and evidence downloads.
- API-level authorization tests for evidence permissions, expired JWT, revoked
  sessions, and disabled users.
- Secure event-to-Stream-Gateway clip request/orchestration, clip upload, and
  `video_clip` EventMedia persistence.
- Dependency probes for PostgreSQL, Redis, RabbitMQ, MinIO, AI Worker, and Stream
  Gateway that issue real authenticated runtime checks.
- Frontend event-detail evidence rendering backed by the evidence API.

## Exact commands executed

```text
npm install --workspace apps/api amqplib@^0.10.9 && npm install --workspace apps/api -D @types/amqplib@^0.10.8  # HTTP 403
npm run lint                                                                                                      # pass
docker --version                                                                                                  # unavailable
docker compose version                                                                                            # unavailable
```

## Production readiness

**NOT PRODUCTION READY.** A real AMQP dependency must be fetched and locked,
then the Compose stack and security/golden-path matrix must be executed before a
production claim can be made. The deterministic provider is an integration fixture,
not production-quality computer vision.
