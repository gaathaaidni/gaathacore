# Sentira AI Security

## Security principles

Phase 10G fixed refresh-token replay caused by bcrypt's 72-byte truncation by using
full-length SHA-256 token digests. Live replay returned HTTP 401.

Sentira AI treats privacy and security as a product capability, not a postscript.

- Use encryption in transit and at rest
- Store secrets in environment variables or secret managers
- Never expose RTSP credentials in browser code
- Enforce tenant-scoped access on every query
- Use least privilege for all roles and services
- Maintain audit trails for sensitive actions
- Validate all input and sanitize outputs

## Recommended controls

## Phase 13 connector controls

The Edge Connector is outbound-only and runs local network probes with explicit CIDR, result-count,
concurrency, and timeout limits. RTSP endpoints reject embedded credentials and redact credentials from
reported URLs. Connector tokens are hashed by the API; revocation clears the hash, and rotation issues a
new one-time token. Disabled connectors fail authentication. The daemon stores its local identity in a
`0600` file and never logs pairing codes or tokens.

The daemon does not accept arbitrary cloud network destinations. ONVIF discovery uses WS-Discovery multicast;
optional RTSP probing requires an explicitly configured bounded network. Physical hardware, DNS rebinding
testing, recorder execution, and stream relay security remain release-gate work.
### Authentication and authorization
- JWT or session-based auth with rotation and expiration policies
- Organization-aware role checks
- Server-side access control enforcement

### Video and media security
- Signed URLs for media access
- Restrict download permissions by role and organization
- Use a secure media gateway instead of direct browser RTSP exposure

### Data protection
- Postgres encryption at rest
- Object storage encryption
- Key management through environment or secret manager

### Platform hardening
- Rate limiting
- Input validation
- SQL injection prevention via ORM/parameterized queries
- CSRF protection where HTTP cookies are used
- XSS protection in frontend rendering

## Retention and privacy

The platform should support configurable retention windows and automated deletion. It should avoid unnecessary biometric or identity inference and should focus on operational events rather than personal behavior profiling.

## Audit log events

The system must record actions such as:
- login/logout
- camera add/remove
- rule creation and modification
- event acknowledge/dismiss/resolve
- permission change
- user creation/deletion
- media download

## Required environment variables

```bash
PORT=3001
DATABASE_URL=postgresql://sentira:sentira_dev_password@localhost:5432/sentira
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minra
MINIO_SECRET_KEY=minra_dev_password
JWT_SECRET=replace-with-secure-secret
```

## Phase 6 credential and tenant controls

Camera passwords use AES-256-GCM through `CAMERA_CREDENTIAL_ENCRYPTION_KEY`. Normal camera APIs omit encrypted passwords and raw credentials. Evidence keys include organization, camera, and event identifiers and are exposed through authenticated/signed access paths rather than guessable public object URLs.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 8 status — PARTIALLY IMPLEMENTED
Refresh tokens are hashed at rest, rotated on use, and revocable per session. Authorization-sensitive control-plane routes use server-side role permissions. Production deployers must set a strong `JWT_SECRET`, `CORS_ORIGINS`, database TLS configuration, and retain no development credentials.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C evidence controls

MinIO access and secret keys are consumed only by the API storage service. Evidence
reads are tenant-filtered before object retrieval and downloaded bytes are
SHA-256-checked when integrity metadata is present.

## Phase 10E storage hardening

The API encodes every opaque S3 object-key component before signing requests, keeping
tenant-scoped evidence paths from being altered by path/query characters. Credentials
remain server-side. Live security, JWT/session, and two-tenant verification remain
blocked and are reported truthfully in `PHASE_10E_COMPLETION_REPORT.md`.
