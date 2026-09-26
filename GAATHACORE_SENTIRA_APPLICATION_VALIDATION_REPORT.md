# GaathaCore Sentira Application Launch Validation Report

- **Date**: 2026-09-25
- **Host**: VPS `srv1520753` (`31.97.230.208`)
- **Repository**: `/root/gaathacore`
- **Git SHA**: `42fdf1efefff8511212a8ef618759f9db99d11f3`
- **Validation Type**: Read-Only Application-Level & Architecture Inspection
- **Overall Status**: **YELLOW** (Core application stack is operational and healthy; public entry wiring, CORS/origin update, and legal document seeding remain before public traffic can be served)

---

## 1. Compliance & Constraint Verifications
* **Source/Config/Nginx Changes**: **NONE** (0 files modified)
* **Database Schema Changes**: **NONE** (0 migrations or DDL executed)
* **User/Data Creation**: **NONE** (0 accounts, records, or test entities created)
* **Container Lifecycle**: **NONE** (0 containers restarted or rebuilt during validation)
* **Scope Integrity**: Suite, POS, and PostPilot remained 100% untouched

---

## 2. Frontend Validation (`127.0.0.1:3010`) — Status: YELLOW
* **HTTP Status**: **HTTP 200 OK**
* **Runtime**: Next.js 15.5.16 (`✓ Starting... ✓ Ready in 2.2s`)
* **Page Title**: `Sentira AI — Intelligent Video Monitoring & Visual Intelligence`
* **Static Assets**: Stylesheets (`/_next/static/css/83b144caee8d6a37.css`), JS chunks, and SVG icons render cleanly without SSR or hydration errors.
* **Navigation & Layout**: Hero section, features, architecture visual, auth actions (`/login`, `/signup`), cookie consent modal, and legal footer render properly.
* **Finding (Action Required)**:
  `sentira_web` was built with build args:
  ```text
  NEXT_PUBLIC_API_URL: https://sentira.gaatha.tech/api
  NEXT_PUBLIC_WS_URL: https://sentira.gaatha.tech
  ```
  Because `sentira.gaatha.tech` is disabled in Nginx, client-side browser JavaScript attempts to reach the legacy domain. For public launch behind `https://gaatha.tech`, the web frontend must be built against the unified public origin (e.g., `https://gaatha.tech/sentira/api` or `/api`), or routed via Nginx.

---

## 3. API Routing Validation (`127.0.0.1:4000`) — Status: GREEN
* **Health Endpoints**:
  * `GET /health` → **HTTP 200 OK** (`{"status":"ok","name":"Sentira AI API"}`)
  * `GET /api/health` → **HTTP 200 OK**
  * `GET /api/v1/health` → **HTTP 200 OK** (`{"service":"sentira-api","status":"healthy"}`)
  * `GET /ready` → **HTTP 200 OK** (`{"status":"ready","features":["auth","multi-tenancy","camera-management","rule-engine","event-service"]}`)
  * `GET /api/legal/documents` → **HTTP 200 OK** (`[]`)
* **Routing Architecture**:
  * NestJS controller routing is prefixed with `/api/...` (e.g. `/api/auth`, `/api/cctv`, `/api/legal`, `/api/analytics`, `/api/audit`).
  * Root health probes (`/health`, `/ready`) are bound at the root for container orchestrators.
  * ValidationPipe is active (`transform: true, whitelist: true`).

---

## 4. Authentication & Signup Flow Analysis — Status: RED (Launch Blocker)
* **Endpoints**:
  * `POST /api/auth/signup`
  * `POST /api/auth/login`
  * `POST /api/auth/refresh`
  * `POST /api/auth/logout`
* **Signup Requirements (`SignupDto`)**:
  * `email`: valid email string
  * `password`: min 8 chars (hashed via bcrypt 10 rounds)
  * `organizationName`: min 2 chars
  * `termsAccepted`: boolean (must be `true`)
  * `privacyAcknowledged`: boolean (must be `true`)
  * `termsDocumentId`: UUID (must reference a published `TERMS_OF_SERVICE` record)
  * `privacyDocumentId`: UUID (must reference a published `PRIVACY_POLICY` record)
* **Root Blocker Identified**:
  * Querying `SELECT count(*) FROM legal_documents;` returned **`0`**.
  * On the web frontend (`apps/web/src/app/signup/page.tsx`), the form checks:
    ```typescript
    if (!termsAccepted || !privacyAcknowledged || !termsDocument || !privacyDocument) {
      setMessage('The current Terms of Service and Privacy Policy must be available and accepted before creating an account.');
      return;
    }
    ```
    Because no published legal documents exist, `termsDocument` and `privacyDocument` are undefined, blocking any user from submitting the signup form.
  * On the API side, `AuthService.signup` queries for `PUBLISHED` documents and throws `409 ConflictException: Current published legal documents are required` if missing.
  * **Required Action**: Seed and publish the standard legal documents (`apps/api/src/database/seeds/legal-documents.ts`) into `legal_documents` table before public launch.

---

## 5. Legal Compliance UI & Configuration — Status: GREEN
* **Verified in `.env`**:
  * `SENTIRA_LEGAL_ENTITY_NAME="GAATHA Ventures Sh.P.K."`
  * `SENTIRA_PRIVACY_EMAIL="gaatha.ro.tech@gmail.com"`
  * `SENTIRA_SUPPORT_EMAIL="gaatha.ro.tech@gmail.com"`
  * `SENTIRA_JURISDICTION="Albania"`
  * `SENTIRA_GOVERNING_LAW="Albania"`
  * `SENTIRA_LEGAL_ENTITY_ADDRESS="Durana Tech Park, Albania"`
  * `SENTIRA_COMPANY_REGISTRATION="M62118505B"`
* **UI Presentation**:
  * Frontend renders standard public pages (`/about`, `/contact`, `/terms`, `/privacy`, `/user-policy`) and Cookie Consent dialog.
  * Document seed templates dynamically inject `GAATHA Ventures Sh.P.K.` and `gaatha.ro.tech@gmail.com`.

---

## 6. Service Integration & Health Logs — Status: GREEN
* **API ↔ PostgreSQL**: 31 tables initialized, connection pool healthy.
* **API ↔ Redis**: Session cache and rate limiting active.
* **API ↔ RabbitMQ**: `[DetectionConsumerService] {"message":"AMQP detection consumer connected","queue":"detection.queue","exchange":"sentira.detections"}`.
* **API ↔ MinIO**: Object storage credentials and endpoint configured for evidence storage.
* **AI Worker**: Consecutive `GET /health` returning 200 OK.
* **Stream Gateway**: Consecutive `GET /health` returning 200 OK.
* **Zero crash loops or unhandled exceptions detected in bounded logs.**

---

## 7. Security & Port Audit — Status: GREEN
* **Port Bindings**:
  * `127.0.0.1:4000` (API) — bound strictly to loopback.
  * `127.0.0.1:3010` (Web) — bound strictly to loopback.
  * Internal services (`postgres:5432`, `rabbitmq:5672`, `redis:6379`, `minio:9000`, `ai_worker:8002`, `stream_gateway:8001`) have **zero public host bindings** (`0.0.0.0`).
* **Pre-Launch Secret Rotation Plan**:
  The following secrets should be rotated in `.env` before public launch:
  1. `SENTIRA_JWT_SECRET`
  2. `SENTIRA_CAMERA_CREDENTIAL_ENCRYPTION_KEY`
  3. `SENTIRA_STREAM_GATEWAY_AUTH_SECRET` & `STREAM_GATEWAY_INTERNAL_TOKEN`
  4. Internal infrastructure passwords (`SENTIRA_POSTGRES_PASSWORD`, `SENTIRA_RABBITMQ_PASSWORD`, `SENTIRA_MINIO_ROOT_PASSWORD`, `SENTIRA_REDIS_PASSWORD`).

---

## 8. Public Entry (`https://gaatha.tech`) Integration Requirements — Status: YELLOW
* **Current Public Entry Architecture**:
  * Nginx proxies `https://gaatha.tech/*` to `127.0.0.1:8765` (`public_entry.py`).
  * `public_entry.py` currently serves a static directory containing links to approved products and rejects undefined subpaths with `404 Not Found`.
  * `PRODUCT_POLICIES` in `public_entry.py` lists Sentira as `CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED`.
* **Changes Required for Public Launch**:
  1. **Nginx Routing**:
     Add location routing in `/etc/nginx/sites-enabled/gaatha.tech`:
     - Route `/sentira/` (or designated subpath) to `http://127.0.0.1:3010`
     - Route `/sentira/api/` to `http://127.0.0.1:4000/api/`
     - Route `/sentira/socket.io/` to `http://127.0.0.1:4000/socket.io/`
  2. **CORS Origins**:
     In `docker-compose.yml`, update `CORS_ORIGINS` for `sentira_api` from `https://sentira.gaatha.tech` to `https://gaatha.tech`.
  3. **Legacy Domain 301 Redirect**:
     In `/etc/nginx/sites-available/sentira.gaatha.tech`, configure:
     ```nginx
     server {
         listen 443 ssl;
         server_name sentira.gaatha.tech;
         return 301 https://gaatha.tech/;
     }
     ```
     and symlink to `sites-enabled`.
  4. **Public Entry Approval**:
     Update `public_entry.py` so Sentira's exposure policy is approved once deployment validation passes.

---

## 9. Launch Blockers Summary & Roadmap to GREEN

| Item | Description | Severity | Remediation |
| :--- | :--- | :--- | :--- |
| **1. Unseeded Legal Documents** | `legal_documents` table has 0 rows; signup fails | **RED** | Run legal document seed and publish `TERMS_OF_SERVICE` & `PRIVACY_POLICY` |
| **2. Client Bundle API Origin** | `sentira_web` built with `NEXT_PUBLIC_API_URL=https://sentira.gaatha.tech/api` | **YELLOW** | Rebuild web with `https://gaatha.tech` origin or map via Nginx |
| **3. API CORS Origin** | `CORS_ORIGINS` set to `https://sentira.gaatha.tech` | **YELLOW** | Update compose to include `https://gaatha.tech` |
| **4. Public Entry & Nginx Wiring**| `gaatha.tech` lacks location proxying to ports 3010 & 4000 | **YELLOW** | Configure Nginx reverse proxy locations and 301 redirect |
