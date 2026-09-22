# GaathaCore Phase 13 Report

**Phase:** 13 - Sentira Service Boundary and Authorization Hardening  
**Date:** 2026-09-22  
**PHASE 13 STATUS: YELLOW**

## Scope and stop conditions

Work was local-only and limited to Gaatha Suite, Gaatha POS, Sentira, PostPilot, and GaathaCore. No VPS access, deployment, DNS/Nginx change, production database or credential change, service restart, commit, push, database merge, Core mapping, Sentira synchronization, PostPilot integration, billing, payment, pricing, subscription, charging, or broad framework rewrite occurred.

The unrelated imported Suite `auto_signup_test.py` collection blocker was not modified.

## Implemented changes

1. Added fail-closed AI Worker service authentication with `X-AI-Worker-Token`.
2. Added worker frame size limits and required non-empty tenant/resource/frame identifiers before decode/inference.
3. Passed the dedicated worker credential from Stream Gateway and removed the worker's host-published Compose port.
4. Removed the Stream Gateway development-token fallback; missing gateway credentials now fail closed.
5. Added clear existing permission guards to dashboard stats, user listing, and demo mutations.
6. Registered `PermissionGuard` dependencies in affected Nest modules.
7. Added matching seeded-admin permissions for `system.admin` and `analytics.view`.
8. Added worker, gateway, global-role, and existing tenant-isolation security tests.

## Remaining security blockers

- Stream Gateway still uses one shared token with no organization or user scope for camera control.
- Internal camera configuration still returns all tenants' decrypted camera credentials to that gateway boundary.
- MediaMTX/WebRTC playback authorization is incomplete and not tenant-isolation verified.
- Rules, zones, and sites need a deliberate permission vocabulary and role migration decision; no ambiguous permissions were invented.
- Connector token endpoints need additional rate-limit, expiry, and replay review.

These blockers prevent a GREEN status and prevent Core mapping from beginning.

## Tenant-isolation results

Passed evidence includes two-organization API lookup isolation, event/media storage namespace isolation, queue tenant-header rejection, inactive-user rejection, invalid internal-token rejection, and worker/gateway credential rejection. Cross-organization gateway control is **not proven** because the current gateway protocol carries no tenant scope; this remains a design blocker rather than a speculative rewrite.

## Exact validation results

- AI worker focused suite: **8 passed, 3 warnings**.
- Stream Gateway focused suite: **7 passed, 1 warning**.
- Sentira API focused suite: **12 passed**.
- Sentira API TypeScript check: **passed**.
- Changed Python compilation: **passed**.
- Compose interpolation using ephemeral local values: **passed**, with no services started.
- `git diff --check`: **passed**.
- Full Sentira API suite: **not run**.
- Docker-backed dependency, migration, WebRTC, and hardware tests: **not run**.
- Repository-wide pytest: still blocked by unrelated imported Suite collection behavior; not modified.

## Files changed

- `.env.example`
- `docker-compose.yml`
- `apps/ai-worker/main.py`
- `apps/ai-worker/tests/test_auth.py`
- `apps/stream-gateway/camera_manager.py`
- `apps/stream-gateway/config.py`
- `apps/stream-gateway/tests/test_stream_gateway.py`
- `apps/api/src/app.module.ts`
- `apps/api/src/auth/guards/permission.guard.spec.ts`
- `apps/api/src/controllers/demo.controller.ts`
- `apps/api/src/database/seed.ts`
- `apps/api/src/modules/dashboard/dashboard.controller.ts`
- `apps/api/src/modules/dashboard/dashboard.module.ts`
- `apps/api/src/modules/users/users.controller.ts`
- `apps/api/src/modules/users/users.module.ts`
- `GAATHACORE_SENTIRA_SECURITY_ASSESSMENT.md`
- `GAATHACORE_PHASE_13_REPORT.md`

All application paths above are under `imported/sentira/sentira-main`; no unrelated product code was changed.

## Production and Core mapping impact

VPS impact: **NONE**. Production readiness: **NOT READY**. Sentira and Core databases remain independent. Core mapping cannot begin until service-scoped gateway authorization, internal camera credential minimization, playback authorization, and the remaining permission contract are resolved.

## Recommended next phase

First approve and implement a tenant-aware Stream Gateway service contract, replace the all-tenant decrypted camera fetch with a least-privilege scoped contract, and verify MediaMTX/WebRTC authorization. Then normalize and approve Sentira permission names and connector-token controls. Only after those controls pass two-organization tests should a separate Core mapping phase be considered.
