# GaathaCore Sentira Integration Assessment

**Assessment date:** 2026-09-22  
**Scope:** local source inspection and focused tests only  
**Overall decision:** Sentira remains independently authenticated and independently persisted. Core integration is designed only; no production adapter or data synchronization is enabled.

## Actual identity and tenant model

Sentira's authoritative tenant is the **organization**. A `User` belongs to one organization through `users.organizationId`. A user has one organization or global role through `roleId`; role permissions are checked against the user's organization. Email is globally unique.

The resource hierarchy is:

`organization -> site -> camera -> event -> event media`

Rules and zones are also organization-scoped and may reference sites or cameras. Events redundantly retain organization, site, and camera IDs so processing can validate all three boundaries. Event media retains organization, event, and camera IDs and uses storage keys under `organizations/{organizationId}/...`.

There is no separate account, project, or tenant entity in Sentira. A site is a location/resource grouping, not a Core project by definition. Core project mapping therefore requires an explicit integration decision and must not be inferred from matching names or IDs.

## Authentication and authorization

### Implemented and verified by source/tests

- Native Sentira authentication is email/password plus access and refresh JWTs.
- Refresh tokens are hashed, persisted, rotated, replay-checked, and revocable.
- JWT claims contain `sub`, email, organization ID, and role ID.
- The JWT strategy now reloads the current user and rejects missing, inactive, or suspended users. It uses current database identity fields rather than trusting stale organization or role claims.
- Permission checks require an organization-scoped role, or an explicitly global role, and verify the role's organization.
- Camera, event, analytics, audit, evidence, onboarding, and connector-management paths use organization predicates or connector-derived organization scope.
- Event media authorization requires media ID, event ID, and authenticated organization ID. Object storage additionally requires the organization-prefixed key.
- WebSocket authentication joins a client only to the JWT organization room.
- Detection processing checks that organization, site, and camera IDs describe the same camera before creating an event.
- Connector registration tokens are hashed and connector operations constrain connector and organization ownership.

### Implemented in this phase

- Added current-user lookup to `JwtStrategy.validate`; inactive access tokens are rejected before request handling.
- Added `JwtAuthGuard`, `PermissionGuard`, and `camera.create` to `POST /api/cctv/connectors/:id/commands`, which previously received `@CurrentUser()` without guards.
- Added focused strategy tests for inactive users and stale JWT claims.

## Tenant isolation findings

| Boundary | Result | Evidence / decision |
|---|---|---|
| Cross-organization API reads | Implemented and tested for cameras, events, media, analytics, onboarding, and connectors | Service queries use authenticated organization scope; existing cross-tenant tests pass. |
| Cross-site camera access | Implemented for normal camera reads; site is checked with organization | Camera queries use both site and organization IDs. |
| Unauthorized event/media access | Implemented for normal API path | Event and media reads include organization predicates and event/media relationship. |
| User deactivation | Hardened in Phase 12 | Access JWT validation now reloads active user state. |
| Rule/zone/site role permissions | Gap remains | Some authenticated routes use JWT only and lack `PermissionGuard`; this is a follow-up security blocker. |
| CCTV command creation | Hardened in Phase 12 | Route now requires native JWT and `camera.create`. |
| AI worker ingress | Blocked | `POST /frames` has no service authentication and accepts caller-supplied tenant/resource IDs. API-side detection validation limits persistence, but not unauthenticated resource consumption or ingress. |
| Stream gateway control | Blocked | A shared internal token protects all camera start/stop/playback/status operations; it carries no organization or user scope. |
| Internal camera configuration | High-risk designed boundary | `/api/cameras/internal/all` returns every tenant's decrypted camera configuration to a holder of the shared gateway token. This must remain private and requires a stronger service authorization design before production. |
| Worker cross-tenant execution | Partial | RabbitMQ requires `x-tenant-id` to equal the detection organization ID and API processing validates camera ownership. Worker ingress itself is not authenticated. |
| Media/object storage | Implemented for API reads | Tenant-prefixed storage keys, authorized metadata lookup, expiry, and SHA-256 verification are present. |

## Database boundary

Sentira owns its own PostgreSQL database, configured as the `sentira` database in its Compose topology. Core owns `gaathacore_core`. The systems have no cross-database joins, foreign keys, or shared business tables in this phase. Sentira TypeORM migrations remain Sentira-owned and include its organizations, users, sites, cameras, events, media, connectors, and operational records.

Sentira UUIDs must not be treated as Core IDs. No Core database was modified and no Sentira business table was copied into Core.

## Candidate Core mappings

All mappings below are **designed only**. A mapping is created only by an explicit operator or controlled provisioning workflow, with source identifiers stored as opaque strings. Mapping ownership is Core integration operations; Sentira remains authoritative for Sentira identity and business records.

| source_service | source_type | source_id | core_id where applicable | mapping ownership | mapping lifecycle |
|---|---|---|---|---|---|
| sentira | user | Sentira `users.id` | Core `users.id` | Core integration operator after identity proof | create explicitly, verify organization membership, revoke on unlink, never infer from email alone |
| sentira | organization | Sentira `organizations.id` | Core `organizations.id` | Core integration operator | create before access, require active organization on both sides, disable/revoke explicitly |
| sentira | site | Sentira `sites.id` | Core `projects.id`, only if approved | Core integration operator | create one explicit project mapping per selected site, reject ambiguous many-to-one mappings, revoke independently |
| sentira | module | literal `sentira` | Core `module_access.module_key = sentira` | Core organization/project administrator | enable or disable per mapped Core organization/project; default disabled |
| sentira | camera | Sentira `cameras.id` | none | Sentira | remains Sentira-owned; use as opaque source identifier in future usage events |
| sentira | event | Sentira `events.id` | none | Sentira | remains Sentira-owned; use as opaque source identifier in future audit/usage metadata |

The Sentira user-to-Core user and organization-to-Core organization mappings are blocked until identity proof, lifecycle ownership, and operator workflow are approved. Site-to-project is ambiguous because a site is not inherently a Core project. Camera and event records must not be copied or represented as Core business records.

## Required adapter boundary

The future adapter must:

1. Accept only an already-authenticated native Sentira request context.
2. Resolve explicit `sentira` source mappings using opaque source IDs.
3. Reject missing, inactive, revoked, or organization-inconsistent mappings.
4. Require Core membership and `module_access` for module key `sentira`.
5. Validate any mapped project belongs to the mapped Core organization.
6. Preserve Sentira's own organization/site/camera/event authorization checks.
7. Never silently create mappings or authorize an unmapped identity.
8. Never join databases or copy Sentira business records into Core.
9. Emit Core audit or future usage events with source identifiers and correlation IDs only after authorization succeeds.

No adapter was implemented because Sentira's authoritative site-to-project meaning and mapping provisioning lifecycle are not yet approved, and service-to-service authorization for the worker/gateway boundary is incomplete.

## Usage-event candidates, without billing

Future Core usage events may describe camera count or active-camera time, event processing, AI analysis, storage bytes, stream processing duration, and alert/incident processing. Candidate source identifiers are `sentira` as `source_service`, the Sentira organization ID, optional site ID, camera ID, event ID, correlation ID, and an idempotency key derived from the source operation.

No prices, plans, invoices, subscriptions, payment providers, wallets, or billing ledger were added.

## Operational review

### Implemented or locally inspectable

- API liveness: `/health`, `/api/health`, and `/api/v1/health`.
- API dependency health: authenticated `/api/system/health` probes PostgreSQL, Redis, RabbitMQ, MinIO, AI Worker, and Stream Gateway.
- AI Worker liveness: `/health`.
- Stream Gateway liveness and metrics: `/health` and `/metrics`; camera controls require the internal token.
- Compose declares PostgreSQL, Redis, RabbitMQ, MinIO, MediaMTX, API, AI Worker, Stream Gateway, RTSP fixture, and web services with local health checks.
- Migration ownership is TypeORM under `apps/api/src/database/migrations`; no Core migration is involved.
- Camera passwords are encrypted at rest in the API database and decrypted only for the internal stream path.

### Designed only or blocked

- No Docker runtime, real camera, external MinIO, RabbitMQ, Redis, MediaMTX, or VPS validation was performed in this phase.
- Compose exposes multiple infrastructure ports for local use and still contains development fallback credentials; production exposure and secret injection require deployment-owner controls.
- AI Worker `/frames` needs authenticated service ingress before production.
- Stream gateway needs tenant-aware authorization or a strictly private network contract before production.
- MediaMTX/WebRTC playback authorization was not proven from the inspected source; do not claim tenant-safe playback at the gateway boundary.
- Worker, queue, object storage, and stream failure behavior is locally represented in code but not externally validated.

## Blockers and next phase

Production readiness remains **not ready**. The security blockers are unauthenticated AI frame ingress, shared-token all-tenant stream control, broad decrypted camera configuration retrieval, missing permission guards on selected authenticated resource-management routes, and the absence of an approved mapping lifecycle.

Phase 13 should not begin product integration or billing. A future phase may first close the service-auth and route-permission blockers, approve Core mapping ownership, and add a narrow adapter with focused two-tenant tests. PostPilot integration remains out of scope.
