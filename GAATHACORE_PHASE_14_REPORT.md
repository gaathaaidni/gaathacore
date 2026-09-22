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
- Added guarded API issuance endpoints for playback, status, start, and stop operations.
- Added 60-second camera/organization/site/operation-scoped HS256 tokens signed with `STREAM_GATEWAY_AUTH_SECRET`.
- Added gateway validation for token issuer, audience, expiry, subject, token ID, camera, organization, site, and requested operation.
- Kept the shared gateway token limited to internal camera loading and aggregate monitoring.

## Actual architecture findings

- The gateway startup contract still loads all enabled cameras for all organizations.
- Gateway start, stop, status, and playback metadata now require short-lived scoped tokens and a matching camera ID.
- Gateway control validates token organization/site claims against cached camera ownership metadata.
- FFmpeg reads camera `streamUrl` directly; credentials are not used by the gateway.
- MediaMTX is declared but not connected to a verified publishing or authorization path.
- WebRTC/HLS URLs are metadata only; no authenticated browser playback route or MediaMTX authorization hook exists.
- Connector pairing is single-use and ten-minute limited; registration tokens are hashed, rotatable, and revocable, but have no expiry or rate limiting.

## Security findings

Improved:

- Internal gateway responses no longer expose encrypted or decrypted camera credentials.
- The gateway still requires its configured service token.
- The AI Worker service token remains separate and required.
- User-facing stream control now follows the API-issued scoped authorization flow.
- Cross-organization, cross-site, wrong-operation, incomplete, invalid, and expired gateway scopes are rejected by focused tests.

Unresolved:

- The shared internal loading contract remains broad by camera count, although secret fields are minimized.
- Scoped control tokens can be replayed within their 60-second lifetime because no shared nonce store exists.
- Playback authorization is absent/unverified.
- Connector token expiry and brute-force controls remain undefined.

## Tenant-isolation evidence

Passed: API two-organization camera/event/evidence isolation, worker tenant-header rejection, invalid/missing service-token rejection, and internal response secret minimization.

Not proven: cross-organization gateway control and playback isolation. The gateway does not receive a tenant-scoped authorization contract, so adding caller-supplied organization headers would be unsafe and was deliberately not done.

## Exact tests and results

- Final API focused suite -> **20 passed**.
- Final API TypeScript check -> **passed**.
- Final Stream Gateway focused suite -> **9 passed, 1 warning**.
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
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/stream-authorization.service.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/stream-authorization.service.spec.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/cameras.controller.ts`
- `imported/sentira/sentira-main/apps/stream-gateway/main.py`
- `imported/sentira/sentira-main/apps/stream-gateway/config.py`
- `imported/sentira/sentira-main/apps/stream-gateway/requirements.txt`
- `imported/sentira/sentira-main/apps/stream-gateway/tests/test_stream_gateway.py`
- `imported/sentira/sentira-main/.env.example`
- `imported/sentira/sentira-main/docker-compose.yml`
- `imported/sentira/sentira-main/docker-compose.production.yml`
- `GAATHACORE_SENTIRA_STREAM_SECURITY_ASSESSMENT.md`
- `GAATHACORE_PHASE_14_REPORT.md`
- `GAATHACORE_PHASE_13_REPORT.md` addendum

## Remaining blockers and next phase

Core mapping cannot begin. The next phase should connect actual MediaMTX/WebRTC playback through the scoped authorization path, define token replay policy, and run live two-organization stream tests. Connector token expiry/rate-limit decisions should be made in the same security design. No PostPilot or billing work is permitted.

## Impact

Database impact: **none**. VPS/production impact: **none**. Production readiness: **NOT READY**.
