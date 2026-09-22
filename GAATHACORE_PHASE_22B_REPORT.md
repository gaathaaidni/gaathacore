# GaathaCore Phase 22B — Four-Product Public Exposure Gates

**Date:** 2026-09-22 (UTC)  
**Mode:** local-only implementation and source review  
**Result:** **PARTIAL — a reusable fail-closed exposure policy is implemented. This is not a production-readiness verdict.**

## Scope and preservation

Phase 22A's dependency-free WSGI directory, exact four-product catalog, public-path allowlist, safe health response, safe 404, and exact-host HTTPS URL validation are preserved. This phase added no deployment, VPS, DNS, Nginx, database, credential, product migration, Core mapping, billing, cross-database join, or shared migration history. Imported Suite `auto_signup_test.py` was not modified. No project beyond Gaatha Suite, Gaatha POS, Sentira, and PostPilot was catalogued.

## Implemented exposure policy

`public_entry.py` now defines an immutable four-product `ProductExposurePolicy` catalog. Every policy has a stable key, display name, source-based reason, required deployment validation, and approved URL configuration mechanism.

A link needs **all** of the following:

1. a code-reviewed policy state of `READY FOR PUBLIC ENTRY`;
2. `public_entry_approved=True` in that policy (an explicit, non-environment approval); and
3. a configured HTTPS URL whose exact host is `app.gaatha.tech` and which has no URL credentials.

Thus, an environment URL alone cannot create readiness or a link. `CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED` products are displayed without links; `NOT READY / DO NOT EXPOSE` products have no URL configuration mechanism at all. All four current policies are fail-closed, so no product is linked by this phase.

## Product exposure matrix

| Product | State | Source evidence | Required deployment validation |
| --- | --- | --- | --- |
| Gaatha Suite | **CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED** | The FastAPI dependency layer obtains an authenticated user and organization, and inspected routes use organization/role dependencies. Static inspection cannot establish route-wide tenant isolation or deployed public behavior. | Verify intended HTTPS entry path, unauthenticated login handoff, and two-organization negative access checks across deployed protected routes. |
| Gaatha POS | **CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED** | Flask-Login unauthorized handling, `current_user.restaurant_id` queries, login-protected dashboard APIs, and permission/admin decorators are present. Full protected-route, KDS/admin/API tenant-negative behavior and deployment routing were not runtime-proven. | Verify intended HTTPS entry path, browser/API unauthorized behavior, and two-restaurant negative checks for POS, KDS, admin, and API routes. |
| Sentira | **CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED** | Phase 21 records source-backed API/gateway authorization hardening but retains a blocked live-media gate. It explicitly does not verify MediaMTX callbacks, HLS playback, WHEP, browser playback, two-tenant live isolation, lifecycle/revocation, or real-camera behavior. | Run those exact media, browser, two-tenant, lifecycle/revocation, and real/remote-camera checks in a disposable deployment-like environment before policy approval. |
| PostPilot | **NOT READY / DO NOT EXPOSE** | Active post CRUD, upload, status, and automation-control routes were found in `app.py`; no sufficiently evidenced authentication, tenant isolation, RBAC, or authorization boundary was found for them. | No public URL may be configured. First implement and test product-owned authentication, authorization, tenant isolation, and safe deployment controls. |

No product is marked READY. This avoids treating static evidence, API tests, or a configured URL as proof of production readiness.

## Files changed

* `public_entry.py`
* `tests/test_public_entry.py`
* `GAATHACORE_PHASE_22B_REPORT.md`

## Tests passed

| Check | Result |
| --- | --- |
| `python -m py_compile public_entry.py tests/test_public_entry.py` | Passed. |
| `python -m pytest -q tests/test_public_entry.py` | Passed: **6 passed**. Covers exact catalog, PostPilot non-linkability, rejected HTTP/wrong-host/internal URLs, conditional URL-bypass prevention, explicit READY approval, safe 404, and safe health output. |
| `cd imported/gaathasuite/gaathasuite-main/frontend && npm run build` | Passed: Vite built successfully. |
| `git diff --check` | Passed. |

## Tests blocked

| Check | Blocker |
| --- | --- |
| `cd imported/gaathapos/gaathapos-main && python -m pytest -q` | Blocked during collection because `flask` is unavailable (`ModuleNotFoundError`). No dependency was installed. |
| Sentira focused API, web, Stream Gateway, and media checks | Not rerun: Phase 21 records unavailable Node/Python dependencies and no Docker-compatible runtime, FFmpeg, or MediaMTX. The phase does not claim runtime media evidence. |

## Tests not run

* No live product, browser, TLS/reverse-proxy, camera, or production probe was run because this phase is local-only.
* No PostPilot smoke test was run because its available paths can trigger real provider posting and are unsafe unattended.
* No full repository test collection was run because it is outside this narrow policy change and prior reports record missing dependencies/unrelated imported Suite collection limitations.

## Public-launch blockers

1. All current policies require deployment/runtime validation before a code-reviewed READY approval can exist.
2. PostPilot requires an access-control design and evidence before it can receive any public URL mechanism.
3. Sentira retains the Phase 21 live-media gate, including MediaMTX authentication, HLS/WHEP/browser playback, two-tenant isolation, lifecycle/revocation, and camera behavior.
4. Suite and POS require independently observed public host/login behavior and tenant-negative route checks; source inspection does not prove route-wide isolation.
5. An operator must validate public reverse-proxy/TLS routing and keep only intended public product paths on `app.gaatha.tech` before any future policy approval.

## Recommended next phase

**Phase 22C — deployment-validation evidence collection, not automatic exposure.** Use a disposable deployment-like environment to execute and record Suite and POS entry/login/two-tenant negative checks, then complete the existing Sentira live-media gate. Keep PostPilot unlinked until it has a product-owned authentication, authorization, tenant-isolation, and RBAC design with focused tests. Only a subsequent code-reviewed policy update, backed by that evidence, may set an individual product to READY.
