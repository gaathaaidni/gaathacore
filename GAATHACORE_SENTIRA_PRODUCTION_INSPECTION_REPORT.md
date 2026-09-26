# GaathaCore Sentira Production Inspection & Diagnostic Report

- **Date**: 2026-09-25
- **Repository**: `/root/gaathacore`
- **Target Host**: VPS `srv1520753` (`31.97.230.208`)
- **Inspection Type**: Read-Only Inventory, Diagnosis, and Architecture Analysis
- **Overall Status**: **RED** (Launch Blocker — Sentira services are stopped/uncreated; database schema uninitialized)

---

## 1. Current Git SHA & Working-Tree State
* **Current HEAD SHA**: `42fdf1efefff8511212a8ef618759f9db99d11f3`
* **Current Branch**: `main`
* **Working-Tree Status**:
  ```text
   M docker-compose.yml
   M imported/gaathapos/gaathapos-main/Dockerfile
   M imported/gaathapos/gaathapos-main/app.py
   M imported/gaathapos/gaathapos-main/extensions.py
   M imported/gaathasuite/gaathasuite-main/Dockerfile
  ?? .dockerignore
  ?? "Compose config: PASS"
  ```
  *(All pre-existing working-tree changes preserved intact; zero files were modified, checked out, or discarded during this inspection).*

---

## 2. Sentira Service Inventory & Current Container State

| Service Name | Container Name | Image | Configured Ports | Current Container Status | Health |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`sentira_redis`** | `gaathacore-sentira_redis-1` | `redis:7-alpine` | `6379/tcp` | **Up 23 hours** | **Healthy** (ping passing) |
| **`sentira_rabbitmq`** | *Not created* | `rabbitmq:3-management` | `5672/tcp, 15672/tcp` | **NOT CREATED** | N/A |
| **`sentira_minio`** | *Not created* | `minio/minio:latest` | `9000/tcp, 9001/tcp` | **NOT CREATED** | N/A |
| **`sentira_mediamtx`** | *Not created* | `bluenviron/mediamtx:latest`| Internal | **NOT CREATED** | N/A |
| **`sentira_api`** | *Not created* | `gaathacore-sentira_api:latest` | `127.0.0.1:4000:4000` | **NOT CREATED** | N/A |
| **`sentira_ai_worker`** | *Not created* | `gaathacore-sentira_ai_worker:latest` | Internal | **NOT CREATED** | N/A |
| **`sentira_stream_gateway`** | *Not created* | `gaathacore-sentira_stream_gateway:latest` | Internal | **NOT CREATED** | N/A |
| **`sentira_web`** | *Not created* | `gaathacore-sentira_web:latest` | `127.0.0.1:3010:3000` | **NOT CREATED** | N/A |

---

## 3. Failed / Stopped Services & Evidence from Bounded Logs
* **`sentira_redis`**: Running and healthy. Logs show clean standalone Redis 7.4.9 startup with password authentication enabled (`Ready to accept connections tcp`).
* **`sentira_rabbitmq`, `sentira_minio`, `sentira_mediamtx`, `sentira_api`, `sentira_ai_worker`, `sentira_stream_gateway`, `sentira_web`**:
  * Bounded logs (`docker compose logs --tail=50 <service>`) returned empty output because containers do not exist in the active Compose project.
  * Root Cause: Operators previously executed selective startups (`docker compose up -d pos_web pos_worker pos_beat` and `docker compose up -d suite_web`) without including Sentira services.

---

## 4. Compose Dependency Chain & Startup Prerequisites

```mermaid
graph TD
    postgres[gaathacore-postgres-1 (Healthy)] --> sentira_api
    sentira_redis[gaathacore-sentira_redis-1 (Healthy)] --> sentira_api
    sentira_rabbitmq[sentira_rabbitmq (Uncreated)] --> sentira_api
    sentira_minio[sentira_minio (Uncreated)] --> sentira_api

    sentira_rabbitmq --> sentira_ai_worker[sentira_ai_worker (Uncreated)]

    sentira_api --> sentira_stream_gateway[sentira_stream_gateway (Uncreated)]
    sentira_ai_worker --> sentira_stream_gateway
    sentira_mediamtx[sentira_mediamtx (Uncreated)] --> sentira_stream_gateway

    sentira_web[sentira_web (Uncreated)]
```

* **Dependency Blockers**:
  1. `sentira_api` cannot start until `sentira_rabbitmq` and `sentira_minio` are created and report healthy.
  2. `sentira_ai_worker` cannot start until `sentira_rabbitmq` is healthy.
  3. `sentira_stream_gateway` cannot start until `sentira_api`, `sentira_ai_worker`, and `sentira_mediamtx` are healthy.

---

## 5. Port & Listener State
* **Port 4000** (`sentira_api` host binding `127.0.0.1:4000`): **CLOSED / Connection Refused** (`curl: (7) Failed to connect to 127.0.0.1 port 4000`).
* **Port 3010** (`sentira_web` host binding `127.0.0.1:3010`): **CLOSED / Connection Refused** (`curl: (7) Failed to connect to 127.0.0.1 port 3010`).
* **Port 6379** (`sentira_redis`): Internal bridge listener active.
* **Ports 5672, 8001, 8002, 8889, 9000, 9001**: Not listening on host or bridge.

---

## 6. Database Connectivity & Migration State (Read-Only)
* **PostgreSQL Database**: `sentira` exists on `gaathacore-postgres-1` (created by `init-databases.sh` and owned by `gaathacore`/`sentira` user).
* **Current Schema Status**:
  * `psql -U gaathacore -d sentira -c "\dt"` returned: **`Did not find any relations.`**
  * Database contains **0 tables, 0 views, 0 migrations recorded**.
* **Migration Mechanism**:
  * TypeORM 0.3.x configured in `apps/api/src/config/database.config.ts`.
  * `migrationsRun: true` and `synchronize: false`.
  * `apps/api/Dockerfile` CMD entrypoint:
    ```bash
    node node_modules/typeorm/cli.js migration:run -d apps/api/dist/data-source.js && node apps/api/dist/main.js
    ```
  * **Pending Migrations**: All 11 migrations are unapplied (including `InitialSchema`, `Phase5EventIntelligence`, `Phase6` through `Phase11`, `CameraOnboarding`, and `LegalCompliance`).
  * When `sentira_api` starts, TypeORM is configured to automatically apply these 11 migrations during bootstrap.

---

## 7. Production & Legal Configuration Status

Inspection of `.env` on VPS revealed:

| Parameter | Required Production Value | Current VPS Value | Status |
| :--- | :--- | :--- | :--- |
| **Entity Name** | `GAATHA Ventures Sh.P.K.` | `Gaatha Ventures Sh p k` | **INCONSISTENT** (Punctuation/casing mismatch) |
| **Jurisdiction** | `Albania` | `Albania` | **GREEN** |
| **Governing Law** | `Albania` | `Albania` | **GREEN** |
| **Address** | `Durana Tech Park, Albania` | `Durana Tech Park, Albania` | **GREEN** |
| **Privacy Email** | `gaatha.ro.tech@gmail.com` | `nexora.gaatha@gmail.com` | **INCONSISTENT** (Legacy Nexora email used) |
| **Support Email** | `gaatha.ro.tech@gmail.com` | `nexora.gaatha@gmail.com` | **INCONSISTENT** (Legacy Nexora email used) |
| **Registration** | `M62118505B` | `M62118505B` | **GREEN** |

---

## 8. Reverse-Proxy & Public Routing Findings
* **Nginx Active Configuration**:
  * `gaatha.tech` & `www.gaatha.tech`: Active in `/etc/nginx/sites-enabled/gaatha.tech`, proxying `443` to `http://127.0.0.1:8765` (`public_entry`).
  * `sentira.gaatha.tech`: Found in `/etc/nginx/sites-available/sentira.gaatha.tech`, but **NOT enabled** (no symlink in `/etc/nginx/sites-enabled/`).
* **External Reachability**:
  * `https://gaatha.tech`: Responds with HTTP 200 via `public_entry`. Sentira is listed as `CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED` (`GAATHA_SENTIRA_PUBLIC_URL` currently unset or unlinked).
  * `https://sentira.gaatha.tech`: Resolves to the VPS IP `31.97.230.208`, but falls through to the default SSL virtual host (`cct.gaatha.tech`) resulting in certificate mismatch / 404.
* **Routing Objective**:
  * Per architecture requirements, `sentira.gaatha.tech` must eventually be replaced by a 301 redirect to `https://gaatha.tech/`.
  * Public access to Sentira must be routed through the single entrypoint `https://gaatha.tech`.

---

## 9. Exact Launch Blockers (RED)
1. **Unstarted Core Infrastructure**: `sentira_rabbitmq`, `sentira_minio`, and `sentira_mediamtx` containers have never been created.
2. **Unstarted Application Services**: `sentira_api`, `sentira_ai_worker`, `sentira_stream_gateway`, and `sentira_web` containers have never been created.
3. **Empty Database**: Database `sentira` exists but contains zero tables; migrations must run on `sentira_api` startup.
4. **Legal / Contact Inconsistencies**: Legacy email addresses (`nexora.gaatha@gmail.com`) and entity name formatting (`Gaatha Ventures Sh p k`) in `.env` must be corrected to match official entity registration.
5. **Public Handoff Routing**: `public_entry.py` requires operational verification and routing configuration to expose Sentira safely behind `https://gaatha.tech`.

---

## 10. Minimum Safe Remediation Sequence (Proposed for Next Phase)
1. **Remediate Legal Configuration**:
   Update `.env` with official entity `GAATHA Ventures Sh.P.K.` and contact `gaatha.ro.tech@gmail.com`.
2. **Launch Infrastructure Prerequisites**:
   Start and verify healthy status for `sentira_rabbitmq`, `sentira_minio`, and `sentira_mediamtx`.
3. **Launch API & Auto-Migrate Database**:
   Start `sentira_api`. Verify TypeORM executes migrations 1–11 cleanly without errors and binds to `127.0.0.1:4000`.
4. **Launch AI Worker & Stream Gateway**:
   Start `sentira_ai_worker` and `sentira_stream_gateway`. Verify healthy internal probes.
5. **Launch Web Frontend**:
   Start `sentira_web` and verify binding to `127.0.0.1:3010`.
6. **Public Entry Integration & Legacy 301**:
   Wire Sentira into `public_entry` and establish the 301 redirect on Nginx for `sentira.gaatha.tech` -> `https://gaatha.tech/`.

---

## 11. Confirmation of Zero Destructive Actions
* **Code Modified**: None (0 files changed).
* **Nginx Modified**: None (0 files changed).
* **Database Altered**: None (Read-only queries only).
* **Secrets Exposed / Rotated**: None (0 secrets printed or modified).
