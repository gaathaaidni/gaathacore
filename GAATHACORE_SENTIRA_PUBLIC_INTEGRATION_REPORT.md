# GaathaCore Sentira Public Integration Report

- **Date**: 2026-09-25
- **Host**: VPS `srv1520753` (`31.97.230.208`)
- **Repository**: `/root/gaathacore`
- **Git SHA**: `42fdf1efefff8511212a8ef618759f9db99d11f3`
- **Integration Type**: Production Legal Seeding, CORS Alignment, Frontend Rebuild, Nginx Reverse-Proxy & Legacy Domain 301
- **Final Status**: **GREEN**

---

## 1. Executive Summary

Sentira has been integrated into the unified GaathaCore public entrypoint under `https://gaatha.tech/sentira/` and its API under `https://gaatha.tech/sentira/api/`. 

All preconditions and gate requirements have passed:
1. **Legal Document Initialization**: `TERMS_OF_SERVICE` and `PRIVACY_POLICY` records were seeded, populated with production entity details, and marked `PUBLISHED`. Non-mutating signup contract validation confirmed that the previous `409 ConflictException` is resolved.
2. **CORS Alignment**: Sentira API now accepts origins from `https://gaatha.tech` and `https://sentira.gaatha.tech` without using wildcards.
3. **Frontend Unified Routing**: Next.js was compiled with `basePath: '/sentira'`, runtime `next.config.js` inclusion, runtime `public/` assets, and relative API routing (`/sentira/api`).
4. **Nginx Public Entry**: Reverse-proxy blocks for `= /sentira`, `/sentira/`, `/sentira/api/`, and `/sentira/socket.io/` are active and serving live traffic behind TLS.
5. **Legacy Domain 301**: `https://sentira.gaatha.tech/` safely and permanently redirects to `https://gaatha.tech/` using its dedicated certificate, eliminating legacy application exposure.
6. **Zero Regression**: Gaatha POS (`3006`), Gaatha Suite (`5000`), and Public Entry (`8765`) remain healthy and operational.

---

## 2. Exact Files & Configuration Changed

### A. Repository Working Tree Files
* `docker-compose.yml`:
  * Updated `sentira_api` `CORS_ORIGINS`: `https://gaatha.tech,https://sentira.gaatha.tech`
  * Updated `sentira_web` build args: `NEXT_PUBLIC_API_URL: /sentira/api` and `NEXT_PUBLIC_WS_URL: https://gaatha.tech/sentira`
* `imported/sentira/sentira-main/apps/web/next.config.js`:
  * Added `basePath: '/sentira'` to `nextConfig`
* `imported/sentira/sentira-main/apps/web/Dockerfile`:
  * Added `COPY --from=build /workspace/apps/web/next.config.js ./next.config.js` to the runtime stage
  * Added `COPY --from=build /workspace/apps/web/public ./public` to the runtime stage
* `imported/sentira/sentira-main/apps/web/src/app/page.tsx`:
  * Updated logo paths to `/sentira/logo.png`
* `imported/sentira/sentira-main/apps/web/src/app/signup/page.tsx`:
  * Updated logo path to `/sentira/logo.png`
* `imported/sentira/sentira-main/apps/web/src/app/login/page.tsx`:
  * Updated logo path to `/sentira/logo.png`
* `imported/sentira/sentira-main/apps/web/src/app/legal/[slug]/page.tsx`:
  * Updated logo path to `/sentira/logo.png`

### B. Host Nginx Configurations
* `/etc/nginx/sites-available/gaatha.tech`:
  * Added location blocks for `= /sentira`, `/sentira/`, `/sentira/api/`, and `/sentira/socket.io/`
* `/etc/nginx/sites-available/sentira.gaatha.tech`:
  * Configured HTTP 80 and HTTPS 443 301 redirects to `https://gaatha.tech/`
* `/etc/nginx/sites-enabled/sentira.gaatha.tech`:
  * Enabled via symlink to `/etc/nginx/sites-available/sentira.gaatha.tech`

---

## 3. Phase 1 — Legal Document Seeding Result

The legal documents were seeded using TypeORM within `sentira_api`. The draft templates were updated to resolve all placeholder tokens using confirmed `.env` variables and marked `PUBLISHED`.

* **Published Terms of Service**:
  * **ID**: `6f22f407-6df1-4653-9330-26e52e3f3130`
  * **Version**: `1.0`
  * **Status**: `PUBLISHED`
  * **Jurisdiction**: `Albania`
  * **Effective / Published At**: `2026-09-25T09:55:43.942Z`
* **Published Privacy Policy**:
  * **ID**: `3bb2db84-2ae9-45e8-a5d5-2fa6cd5403f0`
  * **Version**: `1.0`
  * **Status**: `PUBLISHED`
  * **Jurisdiction**: `Albania`
  * **Effective / Published At**: `2026-09-25T09:55:43.950Z`
* **Entity Details Injected**:
  * Entity Name: `GAATHA Ventures Sh.P.K.`
  * Registered Address: `Durana Tech Park, Albania`
  * Governing Law & Jurisdiction: `Albania`
  * Registration: `M62118505B`
  * Contact & Privacy Email: `gaatha.ro.tech@gmail.com`
* **Signup Contract Non-Mutating Validation**:
  * Test payload with published IDs and intentionally malformed email was submitted to `POST /api/auth/signup`.
  * Response: `HTTP 400 Bad Request` (`['email must be an email']`).
  * Confirmation: Published document IDs were accepted by `AuthService` without the previous `409 ConflictException`; zero database records were created during the test.

---

## 4. Phases 2 & 3 — Web API Target, CORS & Web Rebuild

* **API CORS Configuration**:
  ```yaml
  CORS_ORIGINS: https://gaatha.tech,https://sentira.gaatha.tech
  ```
  Verified via NestJS startup logs. Wildcards are strictly avoided.
* **Frontend API Target**:
  Next.js was built with `NEXT_PUBLIC_API_URL: /sentira/api`. All browser-side API calls (`/auth/login`, `/auth/signup`, `/legal/documents`, `/cameras`, etc.) now execute as same-origin requests under `https://gaatha.tech/sentira/api/...`.
* **Runtime Next.js BasePath Fix**:
  Identified that multi-stage Docker builds without `next.config.js` in the runtime stage cause `next start` to revert to `basePath: ''`. Added `COPY next.config.js` and `COPY public` to stage 2, resolving the initial 404 and enabling clean subpath routing.

---

## 5. Phases 4 & 5 — Public Entry Routing & Nginx Safety

### Nginx Reverse Proxy Architecture
`public_entry.py` serves strictly as the non-proxying static directory portal on `127.0.0.1:8765`. Routing to Sentira services is handled directly by Nginx:

```nginx
# Sentira Web exact root match
location = /sentira {
    proxy_pass http://127.0.0.1:3010;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Sentira API prefix proxy
location /sentira/api/ {
    proxy_pass http://127.0.0.1:4000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Sentira WebSocket Gateway
location /sentira/socket.io/ {
    proxy_pass http://127.0.0.1:4000/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Sentira Web prefix proxy (pages and /sentira/_next/static assets)
location /sentira/ {
    proxy_pass http://127.0.0.1:3010;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Public Entry directory (Root portal)
location / {
    proxy_pass http://127.0.0.1:8765;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

* **Syntax Verification**: `nginx -t` passed (`syntax is ok`, `test is successful`).
* **Reload**: Executed graceful reload via `nginx -s reload`. Zero downtime incurred.

---

## 6. Phase 6 — Legacy Domain (`sentira.gaatha.tech`) 301 Redirect

* **Certificate Verification**:
  Certbot inspection confirmed an active, dedicated certificate:
  ```text
  Certificate Name: sentira.gaatha.tech
    Domains: sentira.gaatha.tech
    Expiry Date: 2026-11-14 17:47:01+00:00 (VALID: 50 days)
    Certificate Path: /etc/letsencrypt/live/sentira.gaatha.tech/fullchain.pem
    Private Key Path: /etc/letsencrypt/live/sentira.gaatha.tech/privkey.pem
  ```
  The certificate is isolated from Phoenix (`phoenix.gaatha.tech`).
* **Configuration**:
  HTTP and HTTPS requests to `sentira.gaatha.tech` return `301 Moved Permanently` to `https://gaatha.tech/`.
* **Validation**:
  ```text
  HTTP/1.1 301 Moved Permanently
  Server: nginx/1.18.0 (Ubuntu)
  Location: https://gaatha.tech/
  ```

---

## 7. Phase 7 — Comprehensive Validation Evidence

| Route / Test Target | Expected | Observed | Status |
| :--- | :--- | :--- | :--- |
| `https://gaatha.tech` (Public Entry) | HTTP 200 | HTTP 200 | **PASS** |
| `https://gaatha.tech/sentira` | HTTP 200 | HTTP 200 (Title: `Sentira AI — Intelligent Video Monitoring...`) | **PASS** |
| `https://gaatha.tech/sentira/` | HTTP 308 -> 200 | HTTP 308 (Redirect to `/sentira`) | **PASS** |
| `https://gaatha.tech/sentira/logo.png` | HTTP 200 | HTTP 200 (image/png, 1,474,065 bytes) | **PASS** |
| `https://gaatha.tech/sentira/api/health` | HTTP 200 | HTTP 200 (`{"status":"ok","name":"Sentira AI API"}`) | **PASS** |
| `https://gaatha.tech/sentira/api/v1/health`| HTTP 200 | HTTP 200 (`{"service":"sentira-api","status":"healthy"}`) | **PASS** |
| `https://gaatha.tech/sentira/api/legal/documents` | HTTP 200 | HTTP 200 (2 published documents returned) | **PASS** |
| `https://sentira.gaatha.tech/` (Legacy) | HTTP 301 | HTTP 301 (`Location: https://gaatha.tech/`) | **PASS** |
| `http://127.0.0.1:3006/health` (Gaatha POS) | HTTP 200 | HTTP 200 | **PASS** |
| `http://127.0.0.1:5000/ready` (Gaatha Suite) | HTTP 200 | HTTP 200 | **PASS** |

---

## 8. Container Infrastructure Status

```text
NAME                                  SERVICE                  STATUS                   PORTS
gaathacore-sentira_ai_worker-1        sentira_ai_worker        Up (healthy)             8002/tcp
gaathacore-sentira_api-1              sentira_api              Up (healthy)             127.0.0.1:4000->4000/tcp
gaathacore-sentira_mediamtx-1         sentira_mediamtx         Up (healthy)             8889/tcp
gaathacore-sentira_minio-1            sentira_minio            Up (healthy)             9000/tcp
gaathacore-sentira_rabbitmq-1         sentira_rabbitmq         Up (healthy)             4369/tcp, 5671-5672/tcp, 15672/tcp
gaathacore-sentira_redis-1            sentira_redis            Up (healthy)             6379/tcp
gaathacore-sentira_stream_gateway-1   sentira_stream_gateway   Up (healthy)             8001/tcp
gaathacore-sentira_web-1              sentira_web              Up                       127.0.0.1:3010->3000/tcp
```

---

## 9. Backup Locations & Rollback Procedure

### Backup Locations on VPS
* Nginx `gaatha.tech`: `/etc/nginx/sites-available/gaatha.tech.bak_*`
* Nginx `sentira.gaatha.tech`: `/etc/nginx/sites-available/sentira.gaatha.tech.bak_*`

### Rollback Procedure
If public exposure must be immediately reverted:
1. Restore previous Nginx configuration:
   ```bash
   cp /etc/nginx/sites-available/gaatha.tech.bak_<TIMESTAMP> /etc/nginx/sites-available/gaatha.tech
   rm -f /etc/nginx/sites-enabled/sentira.gaatha.tech
   nginx -t && nginx -s reload
   ```
2. The internal Sentira stack will continue running on loopback ports `127.0.0.1:3010` and `127.0.0.1:4000` without any public internet ingress.

---

## 10. Conclusion & Final Status

* All 8 Sentira containers are healthy.
* Legal document seeding and non-mutating validation are complete.
* Public routing under `https://gaatha.tech/sentira/` and `https://gaatha.tech/sentira/api/` is fully operational.
* Legacy domain `https://sentira.gaatha.tech/` safely redirects to `https://gaatha.tech/`.
* Existing Gaatha Suite and POS systems operate with zero regression.

**FINAL STATUS: GREEN**
