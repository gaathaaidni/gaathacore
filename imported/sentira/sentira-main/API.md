# Sentira AI API Design

## Base URL

```text
/api
```

## Authentication

### POST /api/auth/login
Creates a session or JWT for the user.

Request body:
```json
{
  "email": "admin@company.com",
  "password": "supersecret"
}
```

### POST /api/auth/logout
Revokes the current session.

### GET /api/auth/me
Returns current authenticated user and permissions.

## Dashboard

### GET /api/dashboard
Returns top-level cards, live alerts, and chart summaries.

## Organizations

### GET /api/organizations
### POST /api/organizations
### GET /api/organizations/:id
### PUT /api/organizations/:id

## Sites

### GET /api/sites
### POST /api/sites
### GET /api/sites/:id
### PUT /api/sites/:id

## Cameras

### GET /api/cameras
### POST /api/cameras
### GET /api/cameras/:id
### PUT /api/cameras/:id
### DELETE /api/cameras/:id
### GET /api/cameras/:id/stream

### Camera onboarding
Onboarding sessions are organization-scoped and expire after 10 minutes. Pairing codes are single-use and hashed at rest.

### POST /api/cameras/onboarding/sessions
Starts an `automatic`, `qr`, or `dvr_nvr` session. Automatic discovery requires a future Sentira Connector inside the customer network.

### GET /api/cameras/onboarding/sessions/:id
### POST /api/cameras/onboarding/sessions/:id/pair
### GET /api/cameras/onboarding/sessions/:id/discovered-cameras
### POST /api/cameras/onboarding/discovered-cameras/:id/claim
Claims a connector-reported camera for the authenticated organization and selected site.

### POST /api/cameras/connectors/register
Connector registration consumes a valid session code and returns a one-time registration token.

### POST /api/cameras/connectors/:id/heartbeat
### POST /api/cameras/connectors/:id/discovered-cameras
Both require the `x-connector-token` header. Connector cameras do not expose local addresses or credentials to browser clients.

### CCTV guided setup and edge connector foundation
- `POST /api/cctv/setup-sessions` - Create a resumable, tenant-scoped setup session.
- `GET /api/cctv/setup-sessions/active` - Resume the current user's active setup session.
- `POST /api/cctv/setup-sessions/:id/connector-pairing` - Create a short-lived single-use edge pairing code.
- `POST /api/cctv/setup-sessions/:id/connector/register` - Edge connector consumes the pairing code and receives a one-time registration token.
- `POST /api/cctv/connectors/heartbeat` - Authenticated connector heartbeat.
- `POST /api/cctv/connectors/discover` - Connector discovery request contract; returns `DISCOVERY_UNAVAILABLE` until an edge discovery agent is connected.
- `POST /api/cctv/connectors/discovery-results` - Authenticated connector reports sanitized local discovery results.
- `POST /api/cctv/connectors/recorder-channels` - Authenticated recorder-channel enumeration contract; returns `CHANNEL_DISCOVERY_UNAVAILABLE` until implemented by the edge connector.
- `POST /api/cctv/setup-sessions/:id/test` - Bounded RTSP/ONVIF or existing-camera verification.
- `GET /api/cctv/setup-sessions/:id/tests` - Tenant-scoped sanitized connection-test history.
- `POST /api/cctv/setup-sessions/:id/complete` - Requires a server-recorded `VERIFIED_CONNECTED` result and matching camera endpoint.

The cloud does not scan private customer networks. Local discovery must run in the authenticated Sentira Edge Connector and report sanitized results outbound.

## Zones

### GET /api/zones
### POST /api/zones
### PUT /api/zones/:id
### DELETE /api/zones/:id

## Rules

### GET /api/rules
### POST /api/rules
### GET /api/rules/:id
### PUT /api/rules/:id
### DELETE /api/rules/:id

## Events

### GET /api/events
### GET /api/events/:id
### POST /api/events/:id/acknowledge
### POST /api/events/:id/resolve
### POST /api/events/:id/dismiss
### POST /api/events/:id/escalate

## Investigation

### GET /api/investigation/search
Query parameters may include date, site, camera, event type, rule, zone, severity, status.

## Analytics

### GET /api/analytics
### GET /api/analytics/reports
### GET /api/reports/:type

## Audit

### GET /api/audit-logs

## Notifications

### GET /api/notifications
### POST /api/notifications/:id/read

## Demo & Testing

### POST /api/demo/generate-event
Creates a single demo event from a specific camera and rule (for sales demos and testing).

Request body:
```json
{
  "cameraId": "camera-uuid",
  "ruleId": "rule-uuid"
}
```

Response: `{ success, event, message }`

### POST /api/demo/trigger-all-rules
Evaluates all organization rules with demo logic (70% trigger probability).

Response: `{ success, eventsCreated, events[] }`

### GET /api/demo/dashboard-data
Returns mock dashboard statistics with demo mode flag.

Response:
```json
{
  "camerasOnline": 128,
  "camerasOffline": 5,
  "eventsToday": 42,
  "criticalEvents": 3,
  "unresolvedEvents": 12,
  "falsePositives": 2,
  "rulesActive": 8,
  "demoMode": true,
  "demoLabel": "DEMO DATA - Simulated Events Only"
}
```

## Health

## Phase 13 connector lifecycle

- `POST /api/cctv/setup-sessions/:id/connector/register` consumes a short-lived pairing code and returns
  the registration token once.
- `POST /api/cctv/connectors/heartbeat` accepts connector metadata and updates the authenticated connector.
- `POST /api/cctv/connectors/discovery-results` accepts bounded, tenant/session-bound discovery results.
- `POST /api/cctv/connectors/:id/revoke` disables a connector and invalidates its token.
- `POST /api/cctv/connectors/:id/rotate` replaces the token and returns the replacement once.

The Phase 13 daemon performs local RTSP/ONVIF endpoint discovery and reports results through these routes.
Recorder enumeration, cloud command polling, and stream relay are not advertised until implemented.
### GET /health
### GET /ready
### GET /metrics

Phase 10G verified live login, refresh rotation with replay rejection, authorized
EventMedia retrieval, and PostgreSQL health. Other dependency probes remain unknown.

`GET /api/system/health` is authenticated. Dependency states are classified as
`HEALTHY`, `DEGRADED`, `UNAVAILABLE`, or `UNKNOWN`; configuration presence alone
does not produce a healthy result. External dependency probes remain pending.

## HTTP status conventions

- 200 OK
- 201 Created
- 204 No Content
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 409 Conflict
- 500 Internal Server Error

## Security requirements

- All authorization must be enforced server-side
- Tenant data must be filtered by organization_id at query scope
- Download and playback routes must require explicit permission checks
- Stream URLs and credentials must never be exposed to the browser API responses in plain form


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 8 control-plane endpoints — IMPLEMENTED, NOT VERIFIED
- `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/sessions`, `DELETE /auth/sessions/:id`
- `GET /api/analytics/overview|events|cameras|rules|sites|sla|alerts`
- `GET /api/audit`
- `GET /api/reports/events.csv`
All `/api` endpoints use bearer JWT authentication and organization scope from the token.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C evidence access

`GET /api/events/:eventId/media/:mediaId` requires the existing `event.view`
permission and returns bytes only when both the event-media record and its event
belong to the authenticated organization. Storage credentials and raw bucket URLs
are not returned.

## Phase 10E evidence behavior

Authorized event-media reads remain API-mediated and organization-filtered; object
storage credentials are never returned to clients. The storage adapter supports
existence and deletion operations internally. Live HTTP authorization and object
storage behavior were not runtime verified in Phase 10E; see
`PHASE_10E_COMPLETION_REPORT.md`.
