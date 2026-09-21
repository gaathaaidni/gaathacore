# Sentira AI — Phase 10B Completion Report

## Status: PARTIALLY VERIFIED

## Architecture and services — IMPLEMENTED

`docker-compose.yml` defines PostgreSQL, Redis, RabbitMQ, MinIO, MediaMTX, API,
Web, AI Worker, and Stream Gateway. Application service dependencies use service
DNS names rather than `localhost`, have restart policies and HTTP/readiness
health checks. The API container runs TypeORM migrations before starting and keeps
`synchronize: false`; the API package has `db:migrate`, `db:revert`, and
`db:migration:status` commands.

## RabbitMQ flow — PARTIALLY IMPLEMENTED

The AI Worker declares durable `sentira.detections` and `detection.queue`, binds
the `detection` routing key, configures a dead-letter exchange, requests publisher
confirms, and publishes persistent normalized envelopes. The API AMQP consumer,
manual acknowledgement/retry policy, and database-backed golden path are **NOT
IMPLEMENTED**. It is incorrect to claim detection-to-rule delivery is verified.

## Redis flow — IMPLEMENTED, NOT LIVE-VERIFIED

Rule temporal state and event deduplication use namespaced Redis keys and Redis
TTL when `REDIS_URL` is configured. The unit-construction fallback is deliberately
limited to isolated tests; Compose supplies `REDIS_URL`. A live Redis restart/TTL
verification is **BLOCKED BY ENVIRONMENT**.

## AI Worker — IMPLEMENTED

The worker exposes `/frames` and `/health`, validates frame identity and base64,
normalizes object fields, and publishes only after inference succeeds. Its explicit
`AI_PROVIDER=deterministic` mode provides predictable CPU-only integration output;
it is not a production model claim.

## Stream Gateway, RTSP fixture, rolling buffer — PARTIALLY IMPLEMENTED

The gateway starts FFmpeg once for JPEG extraction and once for segmented MP4
capture per camera, forwards real JPEG bytes to the worker, watches subprocess
exit, terminates child processes, performs bounded exponential reconnect, and
cleans expired per-camera segments. MediaMTX is included, but a generated RTSP
fixture publisher and live FFmpeg/RTSP exercise are **NOT IMPLEMENTED / BLOCKED
BY ENVIRONMENT**. Configure a test camera with `rtsp://mediamtx:8554/<path>` and
publish a deterministic fixture to that path before running the gateway.

## MinIO flow and evidence clips — NOT IMPLEMENTED

No MinIO SDK transfer, authorized evidence download, EventMedia SHA-256 transfer
record, or rolling-buffer clip assembly has been added. Existing metadata must not
be treated as proof that evidence exists.

## Authentication, RBAC, tenant isolation, WebSocket — PARTIALLY VERIFIED

Existing API unit tests cover selected auth, RBAC wiring, and tenant-scoped service
queries. The requested two-organization HTTP/WebSocket integration suite and
runtime evidence authorization test are **NOT IMPLEMENTED**.

## Health and observability — PARTIALLY IMPLEMENTED

PostgreSQL remains actively probed by the API. Other API dependency statuses remain
`UNKNOWN` until authenticated probes are implemented; Compose health checks test
actual local endpoints rather than declaring configured services healthy.

## Database migrations — PARTIALLY VERIFIED

The controlled migration commands and container startup command are implemented.
Clean-db up/down/up verification is **BLOCKED BY ENVIRONMENT** because Docker is
not available.

## Integration tests, golden path, and failure paths — NOT IMPLEMENTED

Python unit coverage verifies the deterministic model metadata and gateway
supervision/status paths. A Docker-backed golden path (camera through evidence)
and the requested failure-path matrix were not executed and should not be inferred
from configuration.

## Security verification — PARTIALLY VERIFIED

Compose reads secrets from environment substitutions; no new production secret is
committed. Camera credential encryption remains in the API encryption service.
The frontend receives no MinIO credentials. Live authorization and object-storage
verification remain blocked.

## Performance observations and known limitations

No throughput, queue-depth, FFmpeg, or storage measurements were collected. The
main remaining gaps are the API RabbitMQ consumer, MinIO storage/evidence service,
evidence clip orchestration, RTSP fixture publisher, live integration suite, and
external authenticated health probes.

## Verification

- **VERIFIED:** TypeScript lint, API unit tests, production build, Python unit
  tests, and Python compilation (commands below were run in this checkout).
- **BLOCKED BY ENVIRONMENT:** `docker --version` and `docker compose version`
  report `docker: command not found`; no Compose config/build/up/logs, migrations,
  or local services were run.
