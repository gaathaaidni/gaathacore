# GaathaCore Sentira Security Assessment

**Assessment date:** 2026-09-22  
**Phase:** 13 - Sentira Service Boundary and Authorization Hardening  
**Scope:** local source inspection and focused local validation only

## Executive decision

Sentira remains independently authenticated and persisted in its own `sentira` PostgreSQL database. Phase 13 implemented a narrow service-authentication boundary for AI frame ingestion and added clear existing-permission guards to selected API mutations and dashboards.

The system is **not production ready**. Stream Gateway camera control remains protected by one shared token with no organization scope, and the internal camera endpoint still returns all-tenant decrypted camera configuration to that service boundary. Those risks require an explicit service contract and were not changed speculatively.

## Baseline findings

### AI Worker

- `POST /frames` is called only by `apps/stream-gateway/camera_manager.py`.
- Before this phase it had no authentication and accepted caller-supplied organization, site, camera, frame, and timestamp identifiers.
- The worker publishes `x-tenant-id` from `organizationId` to RabbitMQ.
- The API consumer rejects missing or mismatched tenant metadata, and `DetectionProcessorService` verifies the organization/site/camera combination before creating events.
- Those API checks protect persistence but did not protect worker CPU, memory, HTTP ingress, or RabbitMQ publication from an unauthenticated caller.
- Replay protection is not a worker-level guarantee; `frameId` is the message ID and downstream deduplication remains the authoritative event control.

### Stream Gateway

- API camera configuration fetch uses `X-Internal-Token`.
- Gateway control endpoints for playback metadata, start, stop, and status use one `STREAM_GATEWAY_INTERNAL_TOKEN`.
- The gateway stores all fetched cameras and can address any loaded camera by ID; no organization or user scope is carried by the control token.
- MediaMTX/WebRTC/HLS routes are not implemented by the gateway, and no API playback authorization proxy was found. The advertised playback URLs therefore do not constitute verified tenant-aware media authorization.

### Internal camera configuration

- `/api/cameras/internal/all` is protected only by the shared gateway token.
- It returns all cameras and decrypts passwords for the response. The response also includes raw stream URL, username, encrypted password field, organization ID, site ID, and other ORM fields.
- The gateway currently uses `streamUrl` and does not use the returned username/password fields.
- There is no organization or camera filter in this endpoint. A holder of the shared token crosses all tenant boundaries.
- The endpoint is a private-service contract only by convention and Compose networking; it is not proven unreachable outside that network.

### Permission audit

Implemented in this phase where existing permission semantics were clear:

- Dashboard stats now requires existing `analytics.view`.
- User listing now requires existing `system.admin`.
- Demo event mutations now require existing `system.admin`.
- Connector command creation was already hardened in Phase 12 with existing `camera.create`.

Documented but not guessed:

- Rules, zones, and site management lack a consistent existing permission vocabulary. Seed data uses legacy keys such as `rules:write` and `sites:write`, while current guards use dot or colon keys. Adding new permission names without a role migration or product decision would be ambiguous.
- Connector registration, heartbeat, polling, acknowledgement, and result endpoints intentionally use connector registration tokens rather than JWTs. Their token contract remains separate from user authorization and needs rate-limit/replay review before production.

## Implemented changes

### AI Worker service authentication

- Added `X-AI-Worker-Token` validation using constant-time comparison.
- Missing worker configuration, missing headers, and incorrect tokens return `401` and fail closed.
- Added pre-decode encoded-size and post-decode byte-size limits using `AI_MAX_FRAME_BYTES`.
- Added required non-empty tenant/resource/frame identifier validation.
- Passed the dedicated token from Stream Gateway to the worker; it is not logged.
- Made the token required in Compose and explicit in `.env.example`; no credential value was added.
- Removed the host-published AI Worker port from Compose. The worker remains reachable to dependent Compose services by its service network.

The API remains authoritative for organization/site/camera ownership. The worker does not invent or synchronize tenant records.

### Gateway credential fallback

`STREAM_GATEWAY_INTERNAL_TOKEN` no longer defaults to `dev_internal_token`. Missing configuration now fails gateway control requests, and Compose requires the value.

### API permissions

Added existing `PermissionGuard` wiring and decorators to dashboard, user listing, and demo mutation routes. Registered the guard and Role repository in the affected Nest modules. The seeded admin role now includes `system.admin` and `analytics.view` so the new explicit checks do not silently break the seeded administrator.

## Tests and exact results

Passed:

- `cd imported/sentira/sentira-main/apps/ai-worker && PYTHONPATH=. pytest -q tests/test_auth.py tests/test_worker.py tests/test_phase7_models.py tests/test_tracking.py` -> **8 passed, 3 warnings**.
- `cd imported/sentira/sentira-main/apps/stream-gateway && PYTHONPATH=. pytest -q tests/test_stream_gateway.py tests/test_phase7_reliability.py tests/test_fixture_and_buffer.py` -> **7 passed, 1 warning**.
- `cd imported/sentira/sentira-main/apps/api && npm run lint` -> **passed** (`tsc --noEmit`).
- `cd imported/sentira/sentira-main/apps/api && npm test -- --runInBand src/auth/guards/permission.guard.spec.ts src/auth/strategies/jwt.strategy.spec.ts src/modules/cameras/cameras.controller.spec.ts src/services/cross-tenant-isolation.spec.ts` -> **12 passed**.
- `python3 -m py_compile` on changed worker and gateway Python files -> **passed**.
- Compose interpolation with ephemeral local process values -> **passed**; no services were started.
- `git diff --check` -> **passed**.

Not run or blocked:

- Full Sentira API test suite: **not run**.
- Docker-backed Sentira runtime, PostgreSQL migrations, RabbitMQ, Redis, MinIO, MediaMTX, WebRTC, and real-camera tests: **not run**.
- Initial direct worker command without `PYTHONPATH=.` was blocked during collection by the standalone worker import path; the canonical local command passed.
- Repository-wide pytest remains affected by the unrelated imported Suite `auto_signup_test.py` collection blocker; it was not modified.

## Tenant-isolation evidence

- Existing API tests use separate organization IDs and verify camera, event, evidence, and storage lookups remain organization-scoped.
- Existing detection consumer tests reject missing and mismatched `x-tenant-id` before processor invocation.
- Existing camera controller tests reject missing, invalid, and unconfigured internal tokens without calling the sensitive service.
- New worker tests verify missing, invalid, and valid service authentication.
- New gateway tests verify missing, invalid, and valid internal-token behavior.
- The gateway has no organization-scoped credential or ownership query, so cross-organization stream-control isolation is **not proven and remains blocked**.

## Unresolved security risks

1. Stream Gateway control remains all-tenant under a shared token.
2. `/api/cameras/internal/all` returns all-tenant decrypted credentials and broad ORM fields.
3. Worker authentication proves caller service identity but does not independently resolve caller-supplied resource IDs; API validation remains the persistence boundary.
4. MediaMTX/WebRTC playback authorization is not implemented or verified.
5. Rules, zones, and site permission names require an explicit permission contract before additional guards are added.
6. Connector token endpoints need separate rate-limit, expiry, and replay validation.

## Configuration and secrets impact

New required local configuration names:

- `AI_WORKER_INGEST_TOKEN`
- `AI_MAX_FRAME_BYTES` (safe local default: `10485760`)

Existing `STREAM_GATEWAY_INTERNAL_TOKEN` now fails closed when absent. No real or production credential was added, printed, committed, or deployed.

## Database, VPS, and production impact

- Database impact: **none**. No migration, schema, database URL, join, foreign key, or cross-database transaction changed.
- Sentira remains independent from `gaathacore_core`.
- VPS impact: **none**.
- Production impact: **none**. No deployment, DNS, Nginx, production secret, service restart, or production database action occurred.
- Production readiness: **not ready**.

## Core mapping decision

Core mapping remains prohibited for this phase. No Sentira-to-Core adapter, identity mapping, synchronization, or module access write was implemented. The next mapping phase is **not permitted yet** until the gateway/internal-camera service contract and remaining permission vocabulary are approved and tested.
