# GaathaCore Phase 12 Report

**Phase:** 12 - Sentira Identity, Tenant-Boundary and Integration Readiness  
**Date:** 2026-09-22  
**PHASE 12 STATUS: YELLOW**

## Scope and stop conditions

This was a local source-inspection and controlled hardening phase. Only Gaatha Suite, Gaatha POS, Sentira, PostPilot, and GaathaCore were considered. No VPS access, production deployment, DNS/Nginx change, production migration, production credential change, database merge, cross-database join, billing/payment implementation, commit, or push occurred.

## Sentira identity and tenant model

Sentira's authoritative tenant is the organization. Users belong to one organization through `organizationId` and have an organization or global role. Sites belong to organizations. Cameras belong to both an organization and a site. Events belong to an organization, site, and camera. Event media belongs to an organization, event, and camera. Rules and zones are organization-scoped.

Sentira has no authoritative account or project tenant model. Site is a location/resource grouping, not automatically a Core project. The complete mapping and security assessment is in `GAATHACORE_SENTIRA_INTEGRATION_ASSESSMENT.md`.

## Database boundary

Sentira remains in its own `sentira` PostgreSQL database with TypeORM-owned migrations. Core remains in `gaathacore_core`. There are no cross-database joins or foreign keys, no copied Sentira business tables, and no assumption that Sentira UUIDs equal Core IDs.

## Authentication and authorization

Native Sentira authentication remains email/password plus access and refresh JWTs. Refresh tokens are hashed and rotated. Permission guards validate organization-scoped roles. Normal API resource queries use authenticated organization scope; media storage keys are organization-prefixed and read authorization checks organization, event, and media IDs.

Implemented fixes:

- JWT validation reloads the current user and rejects missing, inactive, or suspended users instead of trusting stale access-token identity fields.
- Connector command creation now requires `JwtAuthGuard`, `PermissionGuard`, and `camera.create`.

Remaining findings:

- AI Worker `/frames` has no service authentication.
- Stream Gateway uses one shared token for all-tenant camera controls.
- The internal camera endpoint returns all tenants' decrypted camera configuration to a shared-token holder.
- Rules, zones, and some organization site operations have authenticated routes without permission enforcement.
- MediaMTX/WebRTC tenant-aware playback authorization was not proven.

## Core mapping decision

No Sentira adapter was implemented. Future mappings are designed only:

- Sentira user to Core user: explicit operator mapping; blocked pending identity-proof and lifecycle approval.
- Sentira organization to Core organization: explicit operator mapping; blocked pending lifecycle approval.
- Sentira site to Core project: designed only and ambiguous until site/project semantics are approved.
- Core module: literal `sentira`, disabled by default and enabled only through Core module access.
- Sentira camera and event: remain Sentira-owned source records; no Core business mapping.

Required mapping fields are `source_service`, `source_type`, `source_id`, `core_id` where applicable, mapping ownership, and mapping lifecycle. Missing or inactive mappings must reject access; unmapped identities must never be silently authorized.

## Usage-event candidates

Future non-billing usage boundaries are camera usage, active-camera time, event processing, AI analysis, storage bytes, stream processing, and alert/incident processing. Future source identifiers should include `sentira`, organization ID, optional site ID, camera ID, event ID, correlation ID, and an idempotency key. No billing or pricing was implemented.

## Operational findings

API, AI Worker, and Stream Gateway health endpoints exist. API system health probes PostgreSQL, Redis, RabbitMQ, MinIO, AI Worker, and Stream Gateway. Compose declares the local dependency topology and health checks. Runtime, real-camera, external service, and VPS validation were not performed and are not claimed.

Production readiness remains not ready because service authentication, shared-token blast radius, selected permission gaps, mapping lifecycle, and deployment secret/network controls remain unresolved.

## Tests and exact results

- Sentira focused JWT strategy tests: **2 passed**.
- Sentira existing permission, camera internal-token, and cross-tenant isolation tests: **9 passed**.
- Sentira API TypeScript check: **passed** with `npm run lint`.
- `git diff --check`: **passed**.
- Sentira full API test suite: **not run** in this phase.
- Docker-backed Sentira migration/health checks: **not run** in this phase.
- Core regression, Suite adapter, POS adapter, and operational tests: **not rerun** in this phase; Phase 11 records their prior results.
- Repository-wide pytest remains blocked by the unrelated imported Suite `scripts/auto_signup_test.py` issue documented in Phase 11; it was not modified.

## Files changed

- `imported/sentira/sentira-main/apps/api/src/auth/strategies/jwt.strategy.ts`
- `imported/sentira/sentira-main/apps/api/src/auth/strategies/jwt.strategy.spec.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cctv/cctv.controller.ts`
- `GAATHACORE_SENTIRA_INTEGRATION_ASSESSMENT.md`
- `GAATHACORE_PHASE_12_REPORT.md`
- `GAATHACORE_PHASE_11_REPORT.md` addendum

## VPS and production impact

VPS impact: **NONE**. Production readiness impact: **improved local API hardening, but still NOT READY**. No production action occurred.

## Phase 13 decision

**Do not begin yet.** Close and validate the worker/gateway service-auth boundary, selected permission gaps, and explicit Core mapping lifecycle before implementing a Sentira adapter. Do not begin PostPilot integration or billing in Phase 12 or its immediate follow-up.
