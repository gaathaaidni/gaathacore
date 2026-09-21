# GAATHACORE Phase 2 Report

**Phase:** 2 - Unified Architecture, Code Alignment & Billing Foundation  
**Started:** 2026-09-21  
**Workspace:** `/workspaces/gaathacore`  
**Status:** Complete for the scoped additive alignment slice; broader migrations remain planned

## Executive Summary

Phase 2 establishes an evidence-based path from four independently deployed applications to the GaathaCore platform. The applications remain separate deployables in this phase. No production deployment, VPS change, destructive migration, database merge, credential change, commit, or push is authorized or performed.

Initial inspection confirms the following architecture:

- **Gaatha Suite:** FastAPI/ASGI backend, React/Vite frontend, PostgreSQL/SQLAlchemy/Alembic, Redis-related services, organization-aware application surfaces.
- **Gaatha POS:** Flask/WSGI backend, server-rendered templates and JavaScript, SQLAlchemy/Flask-Migrate, SQLite development and PostgreSQL deployment options, Flask sessions and restaurant-scoped access.
- **Sentira:** NestJS API, Next.js frontend, PostgreSQL/TypeORM migrations, Redis, RabbitMQ, MinIO/S3-compatible storage, MediaMTX, separate AI worker and stream gateway.
- **PostPilot:** Flask backend, HTML/JavaScript frontend, SQLite plus local media/JSON persistence, provider-specific social automation, in-process background threads, and no evidenced authentication or tenant boundary.

The target is a contract-oriented platform layer with canonical identity, organization/project/module context, API versioning, usage metering, auditability, and adapters around existing modules. Framework uniformity and database consolidation are not justified by the current evidence.

## Architecture Before

The four products have separate repositories, runtimes, databases, credentials, authentication mechanisms, deployment topologies, and persistence boundaries. No cross-product database access or shared service contract was found in the Phase 0 inventory.

## Architecture Target

```text
GaathaCore platform contracts
  Identity and organization context
  Project/module authorization
  API envelope, errors, health/readiness, correlation metadata
  Audit and usage-event contracts
  Billing ledger and pricing boundaries
        |
  Authenticated adapters / APIs / webhooks
        |
  Suite | POS | Sentira | PostPilot (independently deployable)
```

The target primary domain remains undecided (`app.gaatha.tech` or `core.gaatha.tech`). Existing product domains remain untouched until a separately approved migration, validation, backup, rollback, and cutover plan is executed.

## Repository Analysis

| Product | Path | Active architecture | Persistence | Async/infrastructure |
|---|---|---|---|---|
| Gaatha POS | `imported/gaathapos/gaathapos-main` | Flask, blueprints, server-rendered UI | SQLAlchemy; SQLite default; PostgreSQL supported; Flask-Migrate/Alembic | Celery/Redis configuration; worker topology requires validation |
| Gaatha Suite | `imported/gaathasuite/gaathasuite-main` | FastAPI backend; React/Vite frontend | Async SQLAlchemy; PostgreSQL; Alembic | Redis/task code; deployed worker requires validation |
| Sentira | `imported/sentira/sentira-main` | NestJS API; Next.js web; separate workers/gateway | TypeORM; PostgreSQL | RabbitMQ, Redis, AI worker, stream gateway, MinIO, MediaMTX |
| PostPilot | `imported/postpilot/postpilot-main` | Flask routes; HTML/JavaScript | SQLite `posts.db`; JSON/local media | In-process Python threads and interval loops |

## Flask/FastAPI Analysis

Gaatha POS and PostPilot use Flask for product-local HTTP and template/API behavior. Gaatha Suite uses FastAPI as its active API layer while retaining legacy Flask-style source areas. Sentira uses NestJS, not Flask or FastAPI. The evidence supports retaining existing frameworks behind a common contract and introducing an API gateway/adapter boundary before any controlled migration. No framework rewrite is performed in this phase.

## Frontend Architecture

- Suite uses React 18 and Vite with compiled assets served by the backend.
- Sentira uses Next.js 14 and React 18.
- POS uses server-rendered templates and JavaScript.
- PostPilot uses HTML/CSS/JavaScript templates.

A shared design token package is not yet present. A cross-product UI rewrite would have high blast radius; alignment should begin with tokens and shell/API contracts at a later implementation step.

## Authentication

- Suite: JWT/password authentication with refresh-cookie and organization-aware dependencies; optional OAuth configuration.
- POS: Flask-Login sessions, password hashing, CSRF, role/permission decorators, restaurant association, and admin behavior.
- Sentira: JWT/Passport, organization context, RBAC, refresh/session records, connector tokens.
- PostPilot: no active user, role, tenant, or authorization model evidenced.

The target model is `User -> Organization -> Project -> Module` with roles and permissions. Existing credentials and sessions must remain valid during migration. PostPilot must not be exposed as a shared public module until an authentication and tenancy boundary exists.

## Multi-Tenancy

Suite and Sentira use organization concepts; POS uses restaurant ownership/scoping; PostPilot has no tenant model. POS has explicit tenant-scoped paths and tests in important inventory areas. Suite and Sentira require broader negative-path verification. No cross-tenant data migration or destructive query change is performed based solely on repository inspection.

## Database Architecture

Separate databases remain the current safe boundary. PostgreSQL is used by Suite and Sentira; POS supports PostgreSQL but defaults to SQLite; PostPilot uses SQLite and local files. IDs, timestamps, tenant fields, model names, and migration systems are not interchangeable. A future consolidation would require mapping tables, dual-read/dual-write or staged export/import, reconciliation, backup/restore rehearsal, and rollback checkpoints.

## Configuration

The Phase 0 inventory identified overlapping names including `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, mail settings, and AI/payment variables. Same-name variables have product-specific semantics and must remain scoped. The target naming convention is documented conceptually as `GAATHACORE_*`, `DATABASE_*`, `REDIS_*`, `JWT_*`, `EMAIL_*`, `STORAGE_*`, `PAYMENT_*`, and `SOCIAL_*`; no live variable is renamed in this phase. Secrets are not copied into this report.

## Integrations

- Suite: Groq AI assistant, SMTP/Resend, Cashfree configuration, local upload storage.
- POS: SMTP, optional Stripe/PayPal, tax/exchange-rate services, local/application storage.
- Sentira: configurable AI provider, email/webhook notification surfaces, MinIO/S3, RTSP/ONVIF, MediaMTX.
- PostPilot: Facebook/Instagram APIs, RSS/news, local image/video generation and media storage.

The future integration layer should expose provider-neutral interfaces and keep provider credentials owned by the responsible service until contracts and secret ownership are approved. No payment charging is enabled or implemented.

## Module Mapping

| GaathaCore area | Current owner | Migration posture |
|---|---|---|
| Core identity, organizations, projects, roles, permissions | Suite/Sentira/POS partial; PostPilot absent | Canonical model and adapters required |
| Business Suite | Gaatha Suite | Retain current service/database; align contracts incrementally |
| POS | Gaatha POS | Retain specialized operational service |
| Sentira | Sentira | Retain specialized visual-intelligence services |
| PostPilot | PostPilot | Isolate until identity, tenancy, durable jobs, and provider security are established |
| Billing/usage | No unified owner; product-local payment/config surfaces | Add immutable event/ledger contract before provider charging |

## Billing / Pay-Per-Use Architecture

The required logical model is:

`Organization -> Project -> Module -> Feature -> User -> Usage Event -> Quantity -> Pricing Rule -> Charge`

The recommended first implementation is an append-only usage-event and billing-ledger contract with idempotency keys, source service, event time, organization/project/module identifiers, quantity/unit, currency, pricing-rule version, and audit metadata. Pricing and charge calculation must be deterministic and replayable. Credits, wallets, subscriptions, invoices, and payments should reference ledger records rather than mutate them. Real payment provider calls remain disabled until an authorized provider and production configuration exist.

## Conflicts Found

| Conflict | Classification | Evidence / decision |
|---|---|---|
| Flask, FastAPI, NestJS runtimes | KEEP ISOLATED initially | Frameworks have different ownership and runtime contracts |
| JWT, session auth, and no auth | REQUIRES MIGRATION | Use gateway/identity adapters; do not destroy existing sessions |
| Organization, restaurant, site, and no tenant concepts | REQUIRES MIGRATION | Define explicit organization/project mapping |
| PostgreSQL, SQLite, local JSON/media | KEEP ISOLATED initially | Do not merge schemas or paths directly |
| Redis, Celery, RabbitMQ, and threads | NEEDS ARCHITECTURAL DECISION | Define event delivery/retry/idempotency before shared queues |
| Provider-specific AI, email, payments, social, storage | SAFE TO ALIGN AT CONTRACT LEVEL | Provider credentials remain service-owned |
| API routes and error envelopes | SAFE TO ALIGN NOW | Add documented versioning and adapter conventions incrementally |
| PostPilot public exposure without auth/tenant controls | SAFE TO ALIGN NOW | Block shared exposure pending security boundary |

## Conflicts Resolved

Initial resolution is architectural: no incompatible runtime, database, credential, or deployment boundary is being silently treated as shared. The following low-risk alignment was implemented:

- Each active service now exposes an additive `/api/v1/health` endpoint with `service`, `status`, and `dependencies` fields.
- Existing unversioned health/readiness endpoints remain unchanged.
- Sentira's existing correlation-ID middleware and health routes remain unchanged.
- A versioned usage-event JSON Schema establishes required organization, module, source-service, quantity, timestamp, and idempotency fields without creating a database table or charging a provider.

## Changes Implemented

- Added `GET /api/v1/health` to Gaatha POS with a live database probe and HTTP 503 on failure.
- Added `GET /api/v1/health` to Gaatha Suite as a liveness contract; dependency state remains `unknown` because the existing `/ready` route owns the database probe.
- Added `GET /api/v1/health` to Sentira and a focused controller assertion; existing `/health`, `/api/health`, and `/ready` routes remain compatible.
- Added `GET /health` and `GET /api/v1/health` to PostPilot with a local SQLite probe. This is an operational probe only and does not make PostPilot safe for public multi-tenant exposure.
- Added `contracts/usage-event.v1.schema.json` as an additive, provider-neutral usage-event contract. It requires an idempotency key and supports optional project/user attribution and metadata.

## Files Modified

- `GAATHACORE_PHASE_2_REPORT.md` created at workspace root before implementation work.
- `contracts/usage-event.v1.schema.json` added.
- `imported/gaathapos/gaathapos-main/app.py` updated with the versioned health route.
- `imported/gaathasuite/gaathasuite-main/backend/app/main.py` updated with the versioned health route.
- `imported/sentira/sentira-main/apps/api/src/app.controller.ts` and `app.service.ts` updated with the versioned health route.
- `imported/sentira/sentira-main/apps/api/src/app.controller.spec.ts` updated with the health contract assertion.
- `imported/postpilot/postpilot-main/app.py` updated with health routes.
- Existing uncommitted Phase 1 files were observed and preserved; they were not authored by this phase.

## Database/Migration Changes

None at phase start. No production database, schema, migration, or data was changed.

## Tests Executed

Executed during Phase 2:

- Workspace git status inspected.
- Phase 0 inventory and master project read.
- `git diff --check`.
- Python bytecode compilation for edited Python trees with `python -m compileall -q`.
- JSON parsing for `contracts/usage-event.v1.schema.json` using Node and Python `json.tool`.
- Sentira API focused test: `npm test -- --runInBand src/app.controller.spec.ts`.
- Sentira API typecheck: `npm run lint`.
- Gaatha Suite frontend build: `npm --prefix frontend run build`.

## Test Results

| Check | Result |
|---|---|
| Python syntax/compile | PASS |
| Usage-event JSON Schema parse | PASS |
| `git diff --check` | PASS |
| Sentira focused health controller test | PASS - 2 tests passed |
| Sentira TypeScript lint/typecheck | PASS |
| Gaatha Suite frontend production build | PASS - Vite build completed |
| Gaatha POS pytest suite | BLOCKED - `pytest` is not installed in the environment |
| PostPilot smoke test | SKIPPED - repository smoke test can perform real external social posts |
| Full four-product test suites | NOT RUN - dependency/runtime setup and external-service safety require separate controlled execution |

## Security Findings

1. PostPilot has no evidenced authentication, authorization, or tenant boundary and must remain isolated from shared public exposure.
2. Cross-product credentials, signing keys, database URLs, storage credentials, and provider tokens must remain service-scoped.
3. Suite and Sentira require broader route-level negative tenant tests before identity consolidation.
4. Existing repository-local artifacts and provider credentials require deployment review; no secret values are included here.

## VPS Deployment Implications

No VPS or public deployment is changed. The future target needs an HTTPS reverse proxy, gateway/API boundary, internal-only PostgreSQL/Redis/queue/storage/media ports, service health/readiness probes, backups, certificates, secret injection, and rollback checkpoints. Existing product deployments remain active until a separately approved cutover.

## Migration Requirements

- Define canonical organization/project/module identifiers and mapping tables.
- Define identity federation/session transition for Suite, POS, Sentira, and PostPilot.
- Establish versioned API, error, health, correlation, audit, and usage-event contracts.
- Prove tenant isolation with negative tests across relevant routes and real-time channels.
- Select durable queue/event strategy with retries and idempotency.
- Rehearse database, object-storage, and media backup/restore before any consolidation.
- Create a UI token/shell package without rewriting product workflows.

## Rollback Considerations

All Phase 2 changes must be additive and reversible. Existing product databases, deployments, authentication, provider credentials, and routes remain the source of runtime truth until an explicit migration is validated. Usage-event writes must be append-only with replay/reconciliation support. No destructive migration, table drop, credential rotation, deployment restart, or public cutover is permitted under this phase scope.

## Remaining Risks

- No single canonical identity provider exists today.
- PostPilot is not ready for shared multi-tenant exposure.
- Full tenant-negative coverage is incomplete across Suite and Sentira.
- Worker deployment and delivery guarantees differ by product.
- Financial data ownership, currency precision, tax treatment, and provider authorization remain undecided.
- Frontend design alignment has not yet been implemented.
- Existing Phase 1 worktree changes must remain distinguishable from Phase 2 changes.
- The new health contract reports liveness for Suite and Sentira with database state `unknown`; readiness endpoints remain the dependency-aware checks.
- The usage-event schema is a contract only. No producer, immutable ledger table, pricing engine, invoice, wallet, credit, or payment integration was added.

## Phase 3 Handoff

Phase 3 adds workspace-level platform contracts and records the migration boundary in `GAATHACORE_PHASE_3_REPORT.md`. Product runtimes, databases, authentication sessions, domains, and deployments remain unchanged. The new API envelope, request context, and audit schemas are additive contracts only; adoption requires product-specific compatibility adapters.

## Recommended Next Phase

Implement and test the additive contract layer: versioned health/readiness metadata, common error and correlation conventions at service boundaries, an isolated usage-event/billing-ledger package or service contract, and focused tenant/auth boundary tests. Then evaluate an authenticated gateway and organization/project mapping without merging product databases.
