# GAATHA ENVIRONMENT & INTEGRATION INVENTORY

**Phase:** 0 - Repository, Environment & Integration Inventory  
**Date inspected:** 2026-09-21  
**Evidence rule:** Repository documentation was compared with active configuration and source where practical. A capability is marked **verified** only when the source/configuration supports it; route or model presence alone is marked **partial** or **requires validation**.

## 1. Purpose

This document records the current environment, architecture, deployment, security, testing, and integration surfaces of the four products governed by `GAATHA_MASTER_PROJECT.md`. It is an evidence baseline for later design work. It does not implement or standardize integrations.

Secret values are intentionally excluded. Only variable names, locations, and purposes are recorded.

## 2. Scope

In scope are exactly these four repositories:

1. Gaatha Suite
2. Gaatha POS
3. Sentira
4. PostPilot

This phase is inspection and documentation only. No application logic, schema, deployment, or production system was changed.

## 3. Repository Locations

| Product | Repository path | Presence |
|---|---|---|
| Gaatha POS | `imported/gaathapos/gaathapos-main` | Confirmed |
| Gaatha Suite | `imported/gaathasuite/gaathasuite-main` | Confirmed |
| Sentira | `imported/sentira/sentira-main` | Confirmed |
| PostPilot | `imported/postpilot/postpilot-main` | Confirmed |

The controlling plan is `GAATHA_MASTER_PROJECT.md` at the workspace root. The requested inventory is this file, `docs/ENVIRONMENT_AND_INTEGRATION_INVENTORY.md`.

## 4. Four Product Overview

### 4.1 Gaatha Suite

Gaatha Suite is a business-management/ERP-oriented SaaS application. The active runtime is FastAPI with a React/Vite frontend. The repository also contains legacy Flask-style modules; repository documentation identifies `backend/app/main.py` as the active application and `backend/main.py` as a compatibility export. Current evidence is strongest for authentication, organization-aware dashboard behavior, health/readiness, legal-acceptance APIs, notifications/preferences, approvals, HR-related routes, vendor/invoice routes, imports/exports, downloads, and AI-assistant routes. CRM, sales, accounting, procurement, inventory, reporting, and other ERP workflows have source or route surfaces but are not all end-to-end verified.

### 4.2 Gaatha POS

Gaatha POS is a Flask and SQLAlchemy restaurant point-of-sale system. Its documented/product surfaces include orders, payments, receipts, tables, split bills, menu, KDS, inventory, recipes, restaurant-scoped users, analytics, tax/currency support, audit logging, imports/exports, and multi-tenant isolation. The repository contains Alembic/Flask-Migrate migrations, Celery configuration, and a broad test suite. Some documents are stale or aspirational, so source and tests take precedence over status claims.

### 4.3 Sentira

Sentira is a multi-tenant visual-intelligence/CCTV platform. The repository is a TypeScript/NestJS API and Next.js web application with separate AI-worker, stream-gateway, and edge-connector areas. Documented and source-supported boundaries include organizations/sites, cameras, zones, rules, events, analytics, evidence/object storage, notifications, audit logs, RTSP/ONVIF onboarding, WebSocket/event updates, RabbitMQ asynchronous work, Redis cache/pub-sub, and MinIO/S3-compatible storage. Some AI and edge production claims remain explicitly incomplete in the repository’s phase reports.

### 4.4 PostPilot

PostPilot is a lightweight Flask content-automation application. The active `app.py` uses SQLite post records, local media directories, JSON-compatible post categories, background threads, and modular Facebook/Instagram/content automation code. The repository contains both a simple content-generation description and a more capable social-posting implementation; the latter is the active source surface. Authentication, tenant isolation, durable worker orchestration, and a production-grade integration boundary are not evidenced.

## 5. Technology Stack

| Product | Backend | Frontend | Data/ORM | Async/background | External/provider surfaces |
|---|---|---|---|---|---|
| Suite | FastAPI, Uvicorn | React 18, Vite | PostgreSQL, SQLAlchemy async, Alembic | Redis configuration; Celery/task code exists, deployed worker not evidenced | SMTP/Resend, optional OAuth, Groq, Cashfree |
| POS | Flask 3, WSGI/Gunicorn-compatible | Server-rendered templates, JavaScript | SQLAlchemy, Flask-SQLAlchemy, SQLite development/PostgreSQL recommended | Celery and Redis configuration; one legacy inventory task is intentionally inert | SMTP, optional Stripe/PayPal, exchange/tax/Sentry configuration |
| Sentira | NestJS 11 | Next.js 14, React 18, TypeScript | PostgreSQL, TypeORM, migrations | RabbitMQ, Redis, Python AI worker, stream gateway | MinIO, MediaMTX, RTSP/ONVIF, configurable AI provider |
| PostPilot | Flask, Gunicorn-compatible | HTML/CSS/JavaScript | SQLite `posts.db`; JSON files remain in repository workflows | Python threads and interval loops | Facebook Graph API, Instagram, RSS/news and local media/video tooling |

## 6. Application Architecture

### Suite

The active ASGI application registers FastAPI routers, middleware, health routes, structured errors, authentication, and static frontend serving. The Docker build compiles the Vite frontend into `backend/static/dist`. Major source areas include `backend/app/routes`, models, migrations, services, legacy `backend/blueprints`, and frontend API clients. The active integration style is HTTP/JSON REST-like routing. Organization scoping is present in selected paths; route-wide isolation and permission coverage remain unproven.

### POS

`app.py` creates the Flask application. `blueprints/` separates admin, auth, API, POS, menu, inventory, KDS, payments, and analytics concerns. `models.py` defines users, restaurants, orders, menu/inventory/payment/audit structures. `services/` contains tax, payment, exchange-rate, and inventory logic. `celery_app.py` and `tasks.py` define background-task surfaces, but the legacy inventory deduction task is a compatibility stub and does not represent an active cross-service event path.

### Sentira

The API owns authentication, tenant-scoped domain services, rule/event lifecycle, notifications, analytics, audit, and connector onboarding. The web app consumes the API and real-time updates. The AI worker and stream gateway are separate deployable components. The architecture documentation describes an asynchronous event path through RabbitMQ, Redis, object storage, and media gateway; the repository phase reports distinguish live-verified components from planned or incomplete production gates.

### PostPilot

`app.py` owns Flask routes, SQLite access, uploads, posting state, and thread startup/control. Social and content modules perform provider calls. The exposed API includes post CRUD by category, start/stop controls, status, search, and upload routes. There is no evidenced service-to-service API, webhook receiver, queue broker, or user/organization boundary.

## 7. Database Inventory

| Product | Engine and access | Important structures/evidence | Tenant/isolation position |
|---|---|---|---|
| Suite | PostgreSQL via async SQLAlchemy; Alembic migrations | Organizations/users, auth/session data, business modules, uploads/download/export support | Organization IDs and scoped routes exist; complete route-by-route isolation is explicitly not proven |
| POS | SQLite by default; PostgreSQL supported/recommended; SQLAlchemy and Alembic | User, restaurant, store settings, menu, order/order items, inventory, recipes, payments, invoices, audit and movement records | Restaurant ownership is enforced in tested inventory paths and query filters; full application coverage should still be validated |
| Sentira | PostgreSQL via TypeORM migrations | Organizations, sites, cameras, zones, rules, events, sessions, audit/evidence metadata | Organization-scoped model and JWT context; full tenant/WebSocket E2E remains a reported validation gap |
| PostPilot | SQLite `posts.db`; migration helper creates a `posts` table; JSON post files also exist | Post ID/type/message/image filename/timestamps; local `posts/` and `images/` storage | No tenant or organization model evidenced |

No cross-product database access was found or introduced. The master plan’s initial separate-database strategy remains consistent with this evidence.

## 8. Authentication / Authorization / Tenancy

- **Suite:** JWT/password authentication and refresh-cookie flow are documented and source-backed. FastAPI dependencies provide role/permission checks, but RBAC matrix coverage and all-route tenant isolation require validation. Optional Google/Microsoft OAuth variables exist. Legal acceptance and audit surfaces exist.
- **POS:** Flask-Login sessions, password hashing, CSRF protection, login-required and role/permission decorators, restaurant association, super-admin behavior, and audit logging are present. 2FA dependencies/configuration are present; production enforcement and current coverage require validation. Tenant isolation is explicit in inventory models/services and tests.
- **Sentira:** JWT with Passport, organization context, RBAC, refresh/session records, server-side permission checks, connector tokens, and encrypted camera credentials are documented/source-supported. Retention, evidence access, and connector pairing controls exist as product surfaces. Full negative tenant tests and full WebSocket E2E remain validation items.
- **PostPilot:** No login, user model, RBAC, tenant model, or authorization middleware is evidenced in the active Flask source. The API routes appear operationally open unless deployment protection exists outside the repository; this requires validation before exposure.

## 9. Environment Variable Inventory

The following is a consolidated inventory of variables discovered in templates or active configuration. Similar names are not assumed to be interchangeable.

| Variable(s) | Product | Consumed/configured in | Purpose and classification |
|---|---|---|---|
| `SECRET_KEY`, `APP_ENV`, `FLASK_ENV`, `BASE_URL`, `CORS_ORIGINS`, `JWT_EXPIRE_MINUTES` | Suite | `backend/config.py`, `.env.example`, Compose | Application/security/origin settings; secret only for `SECRET_KEY`; deployment-dependent |
| `DATABASE_URL`, `DATABASE_HOST`, `DATABASE_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Suite | `backend/config.py`, Compose files | PostgreSQL connection/container settings; password and URL are secret-bearing; production required |
| `REDIS_URL` | Suite | `backend/config.py`, Compose | Redis integration/rate-limit/task configuration; shared candidate only after protocol/ownership validation |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` | Suite | `backend/config.py`, `.env.example` | Initial admin setup; password secret; deployment-dependent |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` | Suite | `backend/config.py`, `.env.example` | Optional OAuth; client secrets secret; optional |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `MAIL_DEFAULT_SENDER`, `RESEND_API_KEY` | Suite | `backend/config.py`, `.env.example` | Email delivery; credentials/API key secret; optional/provider-dependent |
| `GROQ_API_KEY`, `GROQ_MODEL` | Suite | `.env.example` and AI assistant configuration | Groq AI assistant provider; key secret, model non-secret; optional and application-specific today |
| `PAYMENT_PROVIDER`, `CASHFREE_CLIENT_ID`, `CASHFREE_CLIENT_SECRET`, `CASHFREE_ENV`, `CASHFREE_RETURN_URL`, `CASHFREE_NOTIFY_URL` | Suite | `.env.example` and payment configuration | Cashfree payment flow; credentials secret, URLs/config non-secret; webhook verification requires validation |
| `COMPANY_NAME`, `COMPANY_EMAIL`, `COMPANY_WEBSITE`, `COMPANY_JURISDICTION` | Suite | `backend/config.py`, `.env.example` | Display/legal defaults; generally non-secret; legal identity remains to be confirmed |
| `DATABASE_URL`, `SECRET_KEY`, `APP_ENV`, `FLASK_ENV`, `REDIS_URL`, `SESSION_COOKIE_*`, `WTF_CSRF_ENABLED`, `TRUSTED_HOSTS`, `LOG_LEVEL`, `MAX_CONTENT_LENGTH`, `USE_PROXY_FIX` | POS | `config.py`, `.env.example` | Flask/database/session/CSRF/proxy/runtime settings; `SECRET_KEY` and database URL may be secret; requiredness varies by environment |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST_AUTH_METHOD` | POS | `.env.example`, Docker Compose | PostgreSQL container settings; password secret; Docker/deployment only |
| `RATELIMIT_STORAGE_URI`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | POS | `config.py`, `.env.example`, Celery configuration | Redis rate limiting and Celery broker/backend; URLs may contain credentials; optional/configuration-dependent |
| `MAIL_PROVIDER`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | POS | `.env.example`, mail configuration | Password reset/notification email; credentials secret; optional |
| `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | POS | `.env.example` and payment configuration | Optional payment providers; secrets marked by provider; implementation/use requires validation |
| `EXCHANGE_RATE_API_KEY`, `TAX_SERVICE_API_KEY`, `SENTRY_DSN`, `GOOGLE_ANALYTICS_ID` | POS | `.env.example` and related configuration | Optional external rates/tax/monitoring/analytics; API keys/DSN may be secret; application-specific |
| `BABEL_DEFAULT_LOCALE`, `BABEL_DEFAULT_TIMEZONE`, `BABEL_SUPPORTED_LOCALES`, `API_RATE_LIMIT`, `API_TIMEOUT`, `DEBUG`, `TESTING`, `PICKLE_ENABLED`, `PYTHONANYWHERE_DOMAIN`, `ALLOWED_HOSTS`, `PERMANENT_SESSION_LIFETIME` | POS | `.env.example` and configuration | Non-secret runtime, locale, limits, and deployment settings; environment-dependent |
| `NODE_ENV`, `API_PORT`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Sentira | `.env.example`, Compose, API services | API/database runtime; database password secret; required for deployment |
| `JWT_SECRET`, `STREAM_GATEWAY_INTERNAL_TOKEN`, `CAMERA_CREDENTIAL_ENCRYPTION_KEY` | Sentira | `.env.example`, API/stream gateway Compose | Token signing, internal service authentication, camera credential encryption; all secret and required for safe deployment |
| `REDIS_URL`, `RABBITMQ_URL` | Sentira | `.env.example`, Compose, workers/gateway | Cache/pub-sub and asynchronous queue; URLs may contain credentials; service-specific, not automatically shared |
| `MINIO_ENDPOINT`, `MINIO_PORT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | Sentira | `.env.example`, Compose/storage services | Object storage; access credentials secret; Sentira-specific unless a future storage contract is designed |
| `AI_PROVIDER`, `AI_WORKER_URL`, `SENTIRA_API_URL`, `STREAM_SEGMENT_SECONDS`, `STREAM_BUFFER_SECONDS`, `MEDIAMTX_URL`, `BUFFER_ROOT`, `CORS_ORIGINS` | Sentira | `.env.example`, Compose, worker/gateway | AI/stream service endpoints and tuning; endpoints/tuning non-secret, internal token remains secret |
| `FLASK_ENV`, `FLASK_DEBUG`, `HOST`, `PORT`, `WORKERS`, `MAX_CONTENT_LENGTH`, `UPLOAD_FOLDER` | PostPilot | `.env.example`, `app.py`, Compose | Flask/server/upload settings; non-secret except no credential meaning |
| `TOUR_ACCESS_TOKEN`, `TOUR_PAGE_ID`, `VISA_ACCESS_TOKEN`, `VISA_PAGE_ID`, `IG_ACCESS_TOKEN`, `IG_USER_ID` | PostPilot | `.env.example` and social modules | Facebook/Instagram credentials and target IDs; access tokens secret, IDs generally non-secret; application-specific |
| `TOUR_INTERVAL`, `VISA_INTERVAL`, `INSTA_CHECK_INTERVAL`, `FB_PAGE_ID_SUITE`, `INSTA_ID_SUITE` | PostPilot | `.env.example`, `app.py`, Instagram setup | Posting intervals and Instagram target configuration; non-secret except values must be controlled; category-specific |

Actual values, including placeholder credential values from templates, are not reproduced here. Some source files contain fallback configuration or repository-local credential-bearing artifacts; they were not copied into this inventory and should be reviewed separately before deployment.

## 10. External Services & Providers

- **AI:** Gaatha Suite has a Groq configuration (`GROQ_API_KEY`, `GROQ_MODEL`) for its AI assistant. Sentira has an `AI_PROVIDER` abstraction and deterministic local provider configuration; a single commercial provider is not established. POS has no confirmed AI provider. PostPilot contains content automation modules but no confirmed Groq integration.
- **Email:** Suite supports SMTP/Resend configuration. POS documents optional SMTP/mail support. Sentira documents notification channels including email/webhook but the active provider configuration requires validation. PostPilot has no email provider surface evidenced.
- **Payments:** Suite has Cashfree configuration. POS has optional Stripe/PayPal variables and payment models/configuration. No cross-product payment service is established.
- **Social/content:** PostPilot contains Facebook Graph and Instagram integration modules, RSS/news automation, image/video upload and generation paths. No equivalent social provider surface was verified in the other three products.
- **Storage/media:** Suite uses local upload storage volumes. POS is primarily database plus application files. Sentira uses MinIO/object storage, stream buffers, and MediaMTX. PostPilot uses local `images/`, `posts/`, and SQLite files.

No provider standardization was implemented in Phase 0.

## 11. API / Integration Surface

| Product | Existing evidence |
|---|---|
| Suite | FastAPI HTTP routes for auth/profile, organizations, dashboards, health/readiness, legal acceptance, notifications/preferences, approvals, HR, vendors, invoices, imports/exports/downloads, AI assistant, and other registered modules. Exact completion varies by route. Redis Pub/Sub/task code exists; deployed worker is not evidenced. |
| POS | Flask JSON/API blueprints, admin APIs, public API surfaces, authentication flows, menu/inventory/payment/analytics routes, CSV import/export, and smoke/test clients. No external webhook/event contract was verified. Celery configuration exists; the legacy inventory task is intentionally inert. |
| Sentira | REST API under `/api` for auth, organizations/sites, cameras, onboarding/connectors, zones, rules, events, investigation, analytics/reports, audit, notifications, demo, and health. WebSocket/event updates, RabbitMQ work, connector heartbeat/discovery contracts, RTSP/ONVIF and stream gateway boundaries are documented/source-backed. |
| PostPilot | Flask JSON routes for post CRUD, search, upload, start/stop control, and status. Provider clients call Facebook/Instagram externally. No inbound webhook, message broker, durable job queue, or authenticated service API was evidenced. |

Import/export capability is product-local: Suite has file/task/download paths, POS has CSV menu/inventory paths, and PostPilot has local JSON/SQLite/media persistence. None is a cross-product contract.

## 12. Deployment Architecture

- **Suite:** Docker build compiles frontend assets and serves them through FastAPI. Local Compose includes web, PostgreSQL 15, and Redis. Production Compose includes web, PostgreSQL, Redis, named database/upload volumes, readiness health checks, and documented Nginx/VPS/Render/Kubernetes options. Web binds port 5000 internally; production host binding is configurable through `WEB_PORT`. Worker deployment is not evidenced.
- **POS:** Flask development server or WSGI/Gunicorn/PythonAnywhere deployment is documented. Docker Compose defines app, PostgreSQL, and Redis. SQLite is the default development path and PostgreSQL is recommended for production. Celery/Redis configuration exists, but an independently deployed worker/beat topology requires validation. Reverse proxy and PythonAnywhere guidance exist; a single definitive production topology is not established.
- **Sentira:** Docker Compose defines PostgreSQL, Redis, RabbitMQ, MinIO, MediaMTX, API, AI worker, stream gateway, RTSP fixture, and web services. Documented ports include API 4000, web 3000, AI worker 8002, stream gateway 8001, RabbitMQ 5672/15672, MinIO 9000/9001, MediaMTX 8554/8889. Production deployment and Nginx/VPS guidance exist, but phase reports retain runtime/E2E and operational validation gaps.
- **PostPilot:** Dockerfile/Compose and Gunicorn/Nginx/systemd/cloud examples exist. Compose runs one app container on port 5000 with local posts/images/uploads volumes and a status health check. Durable worker separation, external database, reverse proxy in the actual deployed environment, and production secret management require validation.

No service was restarted, redeployed, migrated, or altered.

## 13. Backup / Restore / Migration

- **Suite:** Alembic migrations exist. PostgreSQL and upload volumes are configured. Repository documentation describes backup/restore as an operator procedure; restore rehearsal is explicitly not verified.
- **POS:** Alembic/Flask-Migrate migrations exist, and `pg_backup.sh`/SQLite export tooling is present. Migration and backup scripts are repository evidence, not proof of a completed production restore drill.
- **Sentira:** TypeORM migrations and disaster-recovery/retention documents exist. PostgreSQL, MinIO, and stream-buffer persistence are separate concerns; complete backup/restore execution and evidence retention recovery require validation.
- **PostPilot:** SQLite database and local files are the persistence boundary. A migration helper exists, but backup/restore procedure, consistency guarantees during thread writes, and production recovery are not evidenced.

## 14. Testing & Validation

- **Suite:** Backend/unit/auth/tenant smoke paths, export token scoping, health/readiness, Docker Compose validation, static compile, and frontend production build are documented. Full tenant-negative coverage, accounting balances, procurement, expense workflows, import/export security, worker/Redis operations, backup/restore, and frontend test suite remain gaps.
- **POS:** Pytest tests include currency/tax, endpoint/integration, tenant isolation, payments, checkout, security, inventory integrity, and smoke scripts. Repository documents report passing subsets, but status should be rerun against the current checkout before release.
- **Sentira:** Jest/API and TypeScript/Python checks, build/lint commands, Compose/runtime gates, deterministic RTSP/stream checks, and production-gate reports exist. Full tenant/WebSocket E2E, hardware/edge coverage, evidence-clip orchestration, and some external dependency gates remain explicitly incomplete.
- **PostPilot:** `smoke_test.py` exercises provider posting and upload paths, but it warns that it may perform real external posts; it is not safe to run unattended in this inventory. No comprehensive unit/integration/security suite was evidenced.

No destructive or production-facing tests were run.

## 15. Existing Security Controls

- **Suite:** Required `SECRET_KEY` and `DATABASE_URL` at active config startup, JWT/password auth, refresh handling, CORS/security middleware, structured errors, health/readiness, organization scoping, audit/legal surfaces, and upload/download controls in parts of the application. Route-wide authorization, upload hardening, legal final text, and backup recovery remain risks.
- **POS:** Password hashing, Flask-Login, CSRF, secure/HTTP-only/SameSite session options, trusted hosts/proxy settings, rate-limit configuration, ORM parameterization, RBAC, tenant-scoped inventory constraints, audit logging, and optional 2FA dependencies. Some deployment/security claims in older docs conflict with newer status and require validation.
- **Sentira:** JWT/RBAC, organization scoping, encrypted camera credentials, short-lived pairing codes/tokens, connector tokens, signed/tenant-scoped media intent, retention controls, audit logging, server-side permission checks, health probes, and privacy/security documentation. External production hardening and full E2E isolation remain validation items.
- **PostPilot:** Upload extension/MIME/image-integrity validation, maximum upload size, local path handling, logging, and thread lock for in-memory posting state. No authentication or authorization boundary is evidenced; provider credentials and local artifacts require operational protection.

## 16. Potential Integration Opportunities

These are investigation targets only. No integration was created.

| Relationship | Existing capability | Possible future integration | Status |
|---|---|---|---|
| Suite <-> POS | Suite has organization/business, vendor, invoice, purchasing, inventory/accounting route/model surfaces; POS has restaurant orders, payments, inventory, menu, vendors-like operational data and CSV APIs | Explicit organization/restaurant mapping; controlled inventory, purchasing, vendor, accounting, and reporting APIs/events | Requires contract, identity, currency/tax, and tenant mapping validation |
| Suite <-> Sentira | Suite has organization/user and operational/notification/analytics surfaces; Sentira has organization/site/event/alert/audit APIs | Deliver selected operational alerts/events or aggregate incident intelligence into Suite | Future; no shared event contract exists |
| POS <-> Sentira | POS represents restaurant operations; Sentira represents cameras, rules, events, alerts, and sites | Map restaurant/site identifiers and selected physical-world events to operational notifications | Future; no direct endpoint or event contract exists |
| Suite <-> PostPilot | Suite contains business/content-adjacent data and PostPilot has post CRUD, scheduling/control, and social publishing clients | Approved-content handoff or campaign workflow with explicit approval and outbound publishing boundary | Future; no Suite-to-PostPilot API exists |
| PostPilot <-> other products | PostPilot exposes local REST-like post/control routes and social provider clients | Product-specific approved content export/import or a future integration service | Requires authentication, tenancy, approval, and media contract design |

## 17. Cross-Product Compatibility & Risks

| Area | Evidence-based risk | Assessment |
|---|---|---|
| Authentication | Suite JWT/refresh and organization permissions; POS Flask sessions/roles; Sentira JWT/RBAC/connector tokens; PostPilot no auth evidence | Real incompatibility for direct identity sharing; requires an explicit gateway or federation strategy |
| Tenant model | Suite organizations, POS restaurants, Sentira organizations/sites, PostPilot none | Mapping is possible conceptually but not equivalent; requires a canonical mapping contract |
| Databases/IDs | PostgreSQL/SQLAlchemy, SQLite/SQLAlchemy, PostgreSQL/TypeORM, SQLite/local JSON | Separate stores and ORM/ID conventions; do not share tables; ID and reconciliation rules require validation |
| API conventions | FastAPI routes, Flask blueprints, NestJS `/api`, PostPilot open JSON routes | Different authentication, routing, errors, and lifecycle conventions; adapter/API contracts required |
| Environment names | Multiple `SECRET_KEY`, database, Redis, SMTP/mail names; Sentira internal-service tokens | Same names do not imply same semantics; standardization must be per application |
| Queues/background work | Suite Redis/task code without verified worker, POS Celery, Sentira RabbitMQ/Redis, PostPilot threads | No common queue can be assumed; delivery, retry, idempotency, and scheduling need a boundary |
| Email/AI providers | Suite has Groq and email provider config; POS email and optional external providers; Sentira provider abstractions; PostPilot social APIs | Provider use is application-specific today; shared service is a future option, not current fact |
| Time/currency | POS has locale/timezone/currency and exchange-rate settings; other products have different or less explicit conventions | Cross-product financial/event data needs canonical timezone, currency, and precision rules; requires validation |
| Storage/media | Suite uploads volume, POS local/application storage, Sentira MinIO/stream buffers, PostPilot local files | Media references cannot be exchanged as paths; signed transfer/object contract required |
| Security maturity | Controls and verification depth differ substantially, especially PostPilot and cross-route Suite coverage | Integration must be deny-by-default and independently authenticated |

## 18. Environment Standardization Candidates

### 1. Potentially shared

- Organization-level naming and an integration registration identifier, after a canonical mapping is designed.
- Email delivery service concept, because Suite and POS already have SMTP-style configuration; provider, sender policy, secret ownership, and failure behavior require validation.
- Monitoring/health conventions and correlation IDs, as operational conventions rather than shared credentials.

### 2. Project-specific

- Groq configuration for Suite’s AI assistant.
- Cashfree/Stripe/PayPal payment settings.
- POS currency/tax/exchange settings.
- Sentira JWT, camera encryption, connector token, RabbitMQ, MinIO, MediaMTX, and stream settings.
- PostPilot social access tokens, page/user IDs, posting intervals, and local media paths.

### 3. Must remain isolated

- Database URLs and credentials for all four products.
- JWT/session signing keys, camera encryption keys, connector tokens, and social provider access tokens.
- Private object/media storage credentials and provider-specific payment credentials.
- Product-local worker/broker credentials until a documented shared-service boundary exists.

### 4. Requires further investigation

- Whether any deployment already shares Redis, SMTP, domains, monitoring, or identity outside these repositories.
- Whether Suite’s and POS’s email implementations can use a common provider without changing delivery semantics.
- Whether Sentira AI provider abstraction is intended for a commercial provider in production.
- Whether PostPilot’s provider credentials are fully externalized in the deployed environment.

No environment variable was renamed, copied, or changed.

## 19. Data Ownership Considerations

- Suite should own business organizations, CRM/sales/accounting/procurement/HR records where those workflows are adopted.
- POS should own restaurant operational transactions, menus, orders, payments, KDS state, and restaurant inventory records unless a later contract explicitly delegates selected master data.
- Sentira should own camera/site/rule/event/evidence and retention records.
- PostPilot should own content drafts, publishing state, provider target metadata, and media references for its automation workflow.
- Cross-product identifiers should be explicit mapping records or contract fields. Direct reads of another product’s private tables should remain prohibited by default.

## 20. Preliminary Integration Architecture

The evidence supports the master plan’s direction:

```text
Four independently deployed products
        |
        v
Controlled authenticated APIs / webhooks / selected events
        |
        v
Explicit tenant and identity mapping + versioned data contracts
        |
        v
Coordinated Gaatha ecosystem
```

Recommended initial posture:

- Keep four databases and deployment lifecycles separate.
- Start with read-only or explicitly approved API contracts before write synchronization.
- Use a dedicated integration boundary for authentication, tenant mapping, retries, idempotency, audit, and observability.
- Define ownership for organization, restaurant/site, user, event, inventory, content, and media records before synchronization.
- Treat every existing route as product-local until a versioned external contract is deliberately published.
- Do not merge repositories or introduce a shared queue/storage layer solely for convenience.

## 21. Unknowns / Requires Validation

1. Confirm the active production entrypoints and deployment versions for all four products.
2. Complete route-by-route Suite tenant/RBAC negative testing and resolve legacy Flask/FastAPI runtime ambiguity.
3. Confirm POS’s actual production database, worker/beat deployment, 2FA enforcement, payment-provider usage, and backup restore process.
4. Complete Sentira full tenant/WebSocket E2E, edge connector production behavior, evidence/media recovery, and external provider validation.
5. Establish whether PostPilot is currently protected by an external authentication layer and whether provider credentials are fully environment-managed.
6. Reconcile documented versus source-verified accounting, procurement, CRM, inventory, and reporting workflow maturity in Suite.
7. Define canonical IDs, timezone, currency/precision, error, authentication, and event delivery conventions before integration design.
8. Identify actual deployed email, AI, Redis, storage, and monitoring services; repository configuration alone does not prove shared infrastructure.
9. Review repository-local credential-bearing artifacts and fallback values operationally without copying them into documentation.
10. Validate legal/compliance requirements for India and Europe/Albania before making product or data-sharing claims.

## 22. Phase 0 Findings

- All four in-scope repositories are present at the paths listed above.
- The products are heterogeneous and should remain independently deployable initially.
- Suite and POS have multi-tenancy concepts but different runtime, identity, and tenant models.
- Sentira has the most explicit service/event/media architecture, but several production gates remain open.
- PostPilot has useful outbound social/content capabilities but lacks an evidenced internal security and integration boundary.
- Groq is evidenced for Suite only; Sentira has an AI-provider abstraction; no ecosystem-wide AI provider is established.
- Email configuration is evidenced for Suite and POS; no shared email service is established.
- Existing integration surfaces are product-local HTTP/API, provider clients, queues, background tasks, imports/exports, and Sentira connector/event paths. No cross-product integration currently exists in the inspected evidence.
- The highest risks are identity/tenant mapping, inconsistent security maturity, different storage/database semantics, incomplete worker/backup validation, and unsupported assumptions about shared providers.

## 23. Recommended Next Phase

Before implementation of cross-product features, perform a focused Phase 1 foundation review: verify active deployment entrypoints, close the highest-severity auth/tenant/backup/secret-management gaps per product, and draft versioned contracts for one narrowly chosen read-only integration. Do not begin broad synchronization or repository merging until ownership, identity mapping, security controls, and operational recovery are verified.
