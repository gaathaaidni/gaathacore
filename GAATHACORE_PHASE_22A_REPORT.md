# GaathaCore Phase 22A — Public Launch Readiness Foundation

**Date:** 2026-09-22 (UTC)
**Mode:** implementation-first, local-only
**Result:** **PARTIAL — a fail-closed unified entry callable and local tests are implemented, but it is not connected to the public host in this repository. This is not a production-readiness claim.**

## Scope and architecture inspected

The repository remains a Core Python domain/migration project plus four independently imported products, not an existing unified web runtime. The Phase 0–21 reports and current source were reviewed. The only catalogued products are Gaatha Suite, Gaatha POS, Sentira, and PostPilot. No deployment, VPS, DNS, Nginx, HTTPS, production database, credential, Core mapping, billing, migration history, or imported Suite `auto_signup_test.py` blocker was modified.

The four products retain separate databases and authentication boundaries. The new entry implementation is only a public directory: it does not proxy product traffic, authenticate users, inspect product databases, call product readiness endpoints, or combine product data.

## Implemented

`public_entry.py` adds a dependency-free WSGI callable, `public_entry_app`.

| Route | Behavior |
| --- | --- |
| `/` | GaathaCore-branded directory containing exactly Gaatha Suite, Gaatha POS, Sentira, and PostPilot. |
| `/about`, `/contact`, `/terms`, `/privacy`, `/user-policy` | Conservative public information pages with consistent footer links. No unsupported contact, legal, pricing, integration, or availability claim is made. |
| `/healthz` | Process-only `{"status":"available"}` response; it exposes no dependency, database, URL, or readiness detail. |

Every product has a short source-supported description. By default all cards say **Not yet connected** and render no link. Operators may set `GAATHA_SUITE_PUBLIC_URL`, `GAATHA_POS_PUBLIC_URL`, `GAATHA_SENTIRA_PUBLIC_URL`, or `GAATHA_POSTPILOT_PUBLIC_URL`; a link renders only for HTTPS URLs on the exact launch host `app.gaatha.tech`. Local, private-looking, other-host, credential-bearing, and non-HTTPS values are rejected. A link denotes only that an entry is configured, not that the product is healthy.

`tests/test_public_entry.py` verifies the exact four-product catalog, default unavailable state, URL validation, safe routing, non-disclosing health, and 404 behavior.

## Verified routes and entry points

| Product | Public/source entry evidence | Authentication and tenant evidence | Launch assessment |
| --- | --- | --- | --- |
| Gaatha Suite | FastAPI has `/health`, `/_health`, `/api/v1/health`, and `/ready`; the React client includes public information routes. No deployed `app.gaatha.tech` path was found. | Dashboard work requires an authenticated user and organization context; source-wide authorization coverage is not proven. | Do not mark live or link until public route and auth handoff are deployment-validated. |
| Gaatha POS | Flask has public information pages plus `/health`, `/api/v1/health`, `/ready`, and `/readyz`. | The Flask-Login unauthorized handler redirects HTML users to `auth.login`; business routes use login/role/permission decorators and selected POS routes use Core scope protection. | Redirect behavior is source-backed; full tenant-negative validation and public host mapping remain required. |
| Sentira | Next web has public landing/login/signup/legal pages; Nest API has `/health`, `/api/health`, `/api/v1/health`, and `/ready`. | System health, organizations, dashboard, users, and CCTV APIs use JWT guards; many sensitive controllers also use permission guards. Browser account material is stored in local storage and needs live review. | Keep unconnected pending the Phase 20–21 media/runtime and live-auth gates. |
| PostPilot | Flask has `/`, public information pages, `/health`, `/api/v1/health`, `/api/status`, and post/control/upload APIs. | No login, user, tenant, RBAC, or authorization middleware was evidenced in the active source. | **Unsuitable for public exposure** until authentication, authorization, tenant, CSRF, and deployment boundaries are implemented and tested. |

The directory does not bypass authentication: defaults render no product URL, and a configured URL only navigates to the product's own entry. It never manufactures tokens, forwards credentials, or attempts shared sign-on.

## Health and failure handling

Existing product health/readiness endpoints were inspected but are never called by the directory. This avoids server-side request forgery, internal-topology disclosure, and stale or ambiguous health claims. The public page says **Not yet connected**, never **Available**, until an approved URL is configured. `/healthz` is a directory-process check, not aggregate product readiness.

Existing `core_health` was not integrated because it checks Core PostgreSQL configuration/migration state. No cross-database join, shared migration history, or database access was added.

## Security findings

1. **PostPilot is a launch blocker:** active posting, upload, state, and automation-control APIs have no evidenced application authentication/tenant boundary.
2. **Suite tenant coverage remains incomplete:** selected organization-aware behavior exists, but static inspection cannot prove every route rejects cross-organization access.
3. **Sentira remains yellow:** Phases 20–21 retain blocked media runtime/dependency and unverified live media/auth lifecycle gates.
4. **POS has stronger source-level login and permission evidence**, but public routing deployment and full tenant-negative validation remain unverified.
5. The new directory accepts only exact-host HTTPS values and rejects URL credentials, preventing configured local/internal endpoint disclosure.

## Tests passed

| Check | Result |
| --- | --- |
| `python -m py_compile public_entry.py tests/test_public_entry.py` | Passed. |
| `python -m pytest -q tests/test_public_entry.py` | Passed: 3 tests. |
| Inline WSGI smoke test using a configured Suite URL | Passed: `200 OK`, four cards, approved URL rendered. |
| `cd imported/gaathasuite/gaathasuite-main/frontend && npm run build` | Passed: Vite build completed. |
| Static `rg` route/guard inspection across the four products | Completed; findings recorded above. |
| `git diff --check` | Passed. |

## Tests blocked or not run

| Check | Result and exact blocker |
| --- | --- |
| `python -m pytest -q tests` | Blocked during collection: `flask` is unavailable for Core/POS tests and `fastapi` is unavailable for Suite tests. Five collection errors occurred; the complete suite did not run. |
| `cd imported/sentira/sentira-main/apps/web && npm run build` | Blocked: `next: not found`; Sentira web dependencies are absent. |
| `cd imported/sentira/sentira-main/apps/api && npm run test -- --runInBand` | Blocked: `jest: not found`; Sentira API dependencies are absent. |
| Product live route/auth/readiness probes | Not run: local-only phase; no product runtime was started. |
| Sentira media gate | Blocked as Phase 21 records: no Docker-compatible runtime, FFmpeg, MediaMTX, or required dependencies. |
| PostPilot smoke test | Not run: repository smoke paths may perform real provider posts and are unsafe unattended. |

No dependency was installed or configuration altered to bypass blockers.

## Files changed

* `public_entry.py`
* `tests/test_public_entry.py`
* `GAATHACORE_PHASE_22A_REPORT.md`

## Public-launch risks and deployment validation still required

The entry implementation is **partial**, not a launch completion. Before an operator mounts it at `app.gaatha.tech`, validate:

1. The WSGI callable behind the intended TLS/reverse proxy, including all public routes, `/healthz`, 404 behavior, headers, and cache behavior from an unauthenticated browser.
2. Only independently verified HTTPS `app.gaatha.tech` product paths; each must reach its intended public entry, not an admin/debug/internal endpoint.
3. Product-owned unauthenticated redirect/login paths and negative cross-tenant cases with separate test tenants.
4. PostPilot remains unlinked until its access-control redesign is complete.
5. Sentira's existing local media gate, then live tenant/playback/camera-lifecycle/browser-auth validation before it is linked.
6. Legal text, support ownership, consent, accessibility, monitoring, incident response, backups, secrets, migrations, and rollback with responsible operators. Static inspection and local tests cannot prove these.

## Suggested next implementation phase

**Phase 22B — Authenticated product-entry and exposure gates.** Define and test a deployment-owned allowlisted path contract; complete PostPilot authentication/tenant controls before linking it; then run product tenant-negative tests and the outstanding Sentira media gate. Do not begin Core mapping, live billing, or cross-product database integration.
