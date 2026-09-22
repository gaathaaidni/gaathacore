# GaathaCore Phase 14 Report

**Phase:** 14 - Sentira Tenant-Aware Stream and Camera Credential Boundary  
**Date:** 2026-09-22  
**PHASE 14 STATUS: YELLOW**

## Scope and stop conditions

Local inspection and narrowly scoped hardening only. No VPS access, deployment, service restart, DNS/Nginx change, production database or credential change, commit, push, Core mapping, PostPilot integration, billing, database merge, cross-database join, or speculative framework rewrite occurred.

## Implemented changes

- Replaced the broad internal camera ORM response with a least-field projection containing only camera ID, organization ID, site ID, stream URL, and enabled state.
- Removed internal credential decryption from the gateway configuration retrieval path.
- Added a regression test proving credentials are neither selected in the projection nor decrypted.
- Added `AI_WORKER_INGEST_TOKEN` requirements to `docker-compose.production.yml` for the already-hardened AI Worker boundary.

## Actual architecture findings

- The gateway startup contract still loads all enabled cameras for all organizations.
- Gateway start, stop, status, and playback metadata use one shared token and a camera ID only.
- Gateway control does not perform organization/site ownership checks.
- FFmpeg reads camera `streamUrl` directly; credentials are not used by the gateway.
- MediaMTX is declared but not connected to a verified publishing or authorization path.
- WebRTC/HLS URLs are metadata only; no authenticated browser playback route or MediaMTX authorization hook exists.
- Connector pairing is single-use and ten-minute limited; registration tokens are hashed, rotatable, and revocable, but have no expiry or rate limiting.

## Security findings

Improved:

- Internal gateway responses no longer expose encrypted or decrypted camera credentials.
- The gateway still requires its configured service token.
- The AI Worker service token remains separate and required.

Unresolved:

- Shared gateway credentials remain all-tenant.
- Internal retrieval remains broad by camera count, even though secret fields are minimized.
- Cross-organization stream control is not verifiable with the current protocol.
- Playback authorization is absent/unverified.
- Connector token expiry and brute-force controls remain undefined.

## Tenant-isolation evidence

Passed: API two-organization camera/event/evidence isolation, worker tenant-header rejection, invalid/missing service-token rejection, and internal response secret minimization.

Not proven: cross-organization gateway control and playback isolation. The gateway does not receive a tenant-scoped authorization contract, so adding caller-supplied organization headers would be unsafe and was deliberately not done.

## Exact tests and results

- `cd imported/sentira/sentira-main/apps/api && npm test -- --runInBand src/modules/cameras/cameras.service.spec.ts` -> **5 passed**.
- `cd imported/sentira/sentira-main/apps/api && npm run lint` -> **passed**.
- Focused API authorization/tenant suite from Phase 13 -> **12 passed**.
- `cd imported/sentira/sentira-main/apps/ai-worker && PYTHONPATH=. pytest -q tests/test_auth.py tests/test_worker.py tests/test_phase7_models.py tests/test_tracking.py` -> **8 passed, 3 warnings**.
- `cd imported/sentira/sentira-main/apps/stream-gateway && PYTHONPATH=. pytest -q tests/test_stream_gateway.py tests/test_phase7_reliability.py tests/test_fixture_and_buffer.py` -> **7 passed, 1 warning**.
- Changed Python compilation -> **passed**.
- Local and production Compose interpolation with ephemeral values -> **passed**; no services started.
- `git diff --check` -> **passed**.
- Docker-backed runtime, migration, MediaMTX, WebRTC, and real-camera tests -> **not run**.
- Full Sentira API suite -> **not run**.
- Repository-wide pytest remains blocked by the unrelated imported Suite `auto_signup_test.py`; it was not modified.

## Files changed

- `imported/sentira/sentira-main/apps/api/src/modules/cameras/cameras.service.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/cameras.service.spec.ts`
- `imported/sentira/sentira-main/docker-compose.production.yml`
- `GAATHACORE_SENTIRA_STREAM_SECURITY_ASSESSMENT.md`
- `GAATHACORE_PHASE_14_REPORT.md`
- `GAATHACORE_PHASE_13_REPORT.md` addendum

## Remaining blockers and next phase

Core mapping cannot begin. The next phase should define and implement an API-authorized, short-lived, camera-specific gateway operation contract, then connect actual MediaMTX/WebRTC playback through that authorization path. Connector token expiry/rate-limit decisions should be made in the same security design. No PostPilot or billing work is permitted.

## Impact

Database impact: **none**. VPS/production impact: **none**. Production readiness: **NOT READY**.
