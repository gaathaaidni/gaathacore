# Sentira AI - Phase 11 Implementation Plan

## Scope and gate

Phase 11 will prepare Sentira for `https://sentira.gaatha.tech` as a real
multi-tenant SaaS. It will not start Phase 12 or add unrelated product features.
All runtime and physical-camera results will be reported only after commands or
manual tests actually execute.

## Audit baseline

### Already present

- Organizations, sites, users, roles, cameras, zones, rules, events,
  notifications, audit logs, sessions, and EventMedia entities exist under
  `apps/api/src/entities`.
- JWT login, hashed refresh-token sessions, rotation, replay protection, logout,
  session listing/revocation, RBAC permission guards, and organization-scoped
  service queries exist under `apps/api/src/auth` and `apps/api/src/modules`.
- Camera passwords use the API encryption service and public camera reads omit the
  encrypted password. Internal gateway discovery is token-protected.
- Snapshot upload/download uses the API S3-compatible storage abstraction with
  tenant filtering and integrity metadata.
- The API has event processing, RabbitMQ detection consumption, Redis-backed rule
  state/deduplication, and organization-room WebSocket authentication.
- Compose includes PostgreSQL, Redis, RabbitMQ, MinIO, MediaMTX, API, web, AI
  Worker, Stream Gateway, and deterministic RTSP fixture services.
- The web app has Next.js operations pages for analytics, audit, reports, and
  system health, using bearer-token API requests and explicit loading/error states.

### Missing or incomplete

- No public signup flow creates an organization, owner role, and user in one
  transaction. `POST /api/organizations` is authenticated but does not associate
  the new organization with the caller.
- No subscription, plan, or entitlement model exists. Camera creation in
  `apps/api/src/modules/cameras/cameras.service.ts` has no server-side count
  enforcement; the controller also lacks a tenant-scoped list endpoint and
  permission decorator coverage.
- Camera onboarding has DTO fields for name, site, RTSP URL, credentials, and
  optional metadata, but no complete UI workflow or connection diagnostics.
- WebSocket support currently authenticates the handshake and emits
  `event.created`; `event.updated`, `notification.created`, and `camera.status`
  are not implemented or E2E verified. CORS is currently wildcard.
- `HealthService` actively probes PostgreSQL but returns `UNKNOWN` for Redis,
  RabbitMQ, MinIO, AI Worker, Stream Gateway, and WebSocket.
- Evidence snapshots are implemented; event-triggered clip request, assembly,
  upload, and `video_clip` EventMedia persistence are absent.
- The frontend is an operations scaffold. Login, signup, organization context,
  camera management, event detail, and evidence UI are absent.
- Compose currently publishes PostgreSQL, Redis, RabbitMQ management, and MinIO
  ports; production deployment needs a private internal network and reverse proxy
  exposure limited to HTTPS application traffic.
- Phase 10G verified the deterministic fixture path, not a physical CCTV camera.

## Implementation workstreams

### 1. SaaS identity and organization onboarding

- Add a public signup DTO/controller path that validates email/password,
  organization name, and creates organization, owner role, and user transactionally.
- Reuse `AuthService` for initial token/session issuance; do not create a second
  authentication service.
- Ensure organization reads, site creation, dashboard, and all resource routes
  derive organization scope from the authenticated user.
- Add integration tests for signup, login, disabled users, refresh rotation/replay,
  logout, session listing, and invalid/expired tokens.

Primary surfaces: `apps/api/src/auth`,
`apps/api/src/modules/organizations`, `apps/api/src/entities`, migrations,
and `apps/api/test/integration`.

### 2. Extensible camera entitlement

- Extend `Organization` with a plan/entitlement representation because no
  subscription model currently exists. Use a future-proof plan key plus a persisted
  camera limit, with the free plan defaulting to 3.
- Centralize limit lookup in one entitlement service/policy; do not scatter the
  value `3` through controllers or UI.
- Enforce the limit inside the camera creation transaction using a concurrency-safe
  count/lock strategy. Return a typed business error code `CAMERA_LIMIT_REACHED`
  and the required contact-us message.
- Add tenant-scoped camera list/detail/status endpoints and permission checks.
- Add migration and reversible down implementation for the entitlement fields.

Primary surfaces: `Organization` entity, new entitlement service within the API
module boundary, `CamerasService`, `CamerasController`, migration, and API tests.

### 3. Camera onboarding and diagnostics

- Complete API DTO validation for RTSP URL, site ownership, enabled state, and
  optional credentials.
- Preserve AES-256-GCM encryption and ensure create/list/detail responses never
  include password or decrypted credentials.
- Add an authenticated diagnostic path that returns connection state, FFmpeg
  classification, and AI-processing state without returning secrets.
- Add deterministic tests for credential non-disclosure and invalid tenant/site
  combinations.

### 4. Tenant and RBAC security suite

- Add a dedicated live integration suite using two independent organizations and
  users. Cover direct IDs and list/query paths for cameras, zones, rules, events,
  notifications, analytics, audit records, and EventMedia.
- Verify both HTTP denial behavior and evidence download denial. Preserve 404/403
  semantics intentionally rather than weakening guards.
- Add real Socket.IO client tests for valid token, invalid token, wrong organization,
  and event isolation.
- Add missing event broadcast types only where existing domain transitions produce
  them; do not emit fabricated events.

Primary surfaces: `apps/api/test/integration`, `events.gateway.ts`, existing
controllers/services, and test-only Compose orchestration.

### 5. Evidence closure decision

- First audit whether a secure gateway callback/upload contract can be added without
  creating a second storage abstraction.
- If safe, add authenticated API-to-gateway clip request, bounded segment selection,
  FFmpeg assembly, API upload, EventMedia persistence, cleanup, and tenant/camera
  checks.
- Otherwise keep clips explicitly NOT IMPLEMENTED and document the exact missing
  contract. Never create placeholder or fabricated video.
- Add frontend event detail and authorized snapshot/media retrieval only after the
  API contract is stable.

### 6. Health and observability

- Extend `HealthService` with safe internal probes for Redis, RabbitMQ, MinIO, AI
  Worker, and Stream Gateway using service credentials/tokens already held by the
  API process. Preserve `HEALTHY`, `DEGRADED`, `UNAVAILABLE`, and `UNKNOWN`.
- Keep `/health` and `/ready` suitable for unauthenticated infrastructure checks;
  keep detailed dependency health authenticated.
- Add correlation IDs to diagnostic requests and verify they appear in relevant
  logs without secrets.

### 7. Production deployment hardening

- Add a production Compose profile or deployment configuration for
  `sentira.gaatha.tech` with no committed secrets, persistent volumes, resource
  limits, restart policies, backups, and private infrastructure networking.
- Remove unnecessary public bindings for PostgreSQL, Redis, RabbitMQ management,
  MinIO, and MediaMTX in the production topology. Expose only reverse-proxy HTTPS
  routes for web/API and explicitly controlled streaming endpoints.
- Define reverse-proxy/TLS/DNS requirements and validate CORS against the production
  origin rather than wildcard defaults.
- Review firewall rules, log retention, backup/restore, and secret rotation
  procedures. These require deployment-host verification and cannot be proven in
  this workspace alone.

### 8. Frontend SaaS workflow

- Implement real signup/login/session handling against the API.
- Add organization context, camera list/add flow, entitlement count and contact-us
  message, camera status/AI state, events list/detail, and authorized evidence
  access.
- Remove demo/placeholder claims from user-facing SaaS paths. Preserve explicit
  loading, empty, unauthorized, and service-error states.
- Validate contracts against the live API; use browser automation only if available.

## Verification order

1. Run existing unit and Python suites.
2. Add and run entitlement, credential, auth/session, tenant, evidence, WebSocket,
   and health tests.
3. Run migration up/down/up on a clean database.
4. Build and start the production-like Compose profile with ephemeral test secrets.
5. Run live signup, two-tenant HTTP/RBAC, EventMedia, WebSocket, health, and
   failure/recovery checks.
6. Run deterministic RTSP checks and reserve physical CCTV verification for the
   local camera owner/manual environment.
7. Run frontend API/browser checks and conservative performance measurements.
8. Create `PHASE_11_COMPLETION_REPORT.md` with separate IMPLEMENTED, VERIFIED,
   PARTIALLY VERIFIED, BLOCKED, NOT IMPLEMENTED, SECURITY, PERFORMANCE,
   REMAINING RISKS, and PRODUCTION READINESS sections.

## Acceptance gate

Phase 11 may not claim production readiness until the evidence supports code
completion, automated tests, Docker runtime, cross-service E2E, tenant isolation,
security review, deployment configuration, and the physical-camera validation
status is explicitly recorded. The physical camera may remain pending manual
verification without blocking code work, but it must never be claimed as tested.
