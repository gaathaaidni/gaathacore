# GAATHACORE PHASE 15 REPORT

Date: 2026-09-22
Scope: Sentira only
Status: BLOCKED FOR LIVE PLAYBACK AUTHORIZATION

## Executive Result

Phase 15 stopped without connecting browser playback to production behavior. Sentira has a native API authorization endpoint and a Stream Gateway scoped JWT verifier, but no verified end-to-end browser media path. WHEP and HLS values are metadata only in the current source. Core mapping remains blocked and production readiness is not claimed.

## Actual Architecture

- API: NestJS camera routes issue 60-second HS256 scoped tokens after native JWT and `camera.view`/`camera.create` permission checks. Camera, organization, and site are looked up server-side.
- Next.js: dashboard source loads camera metadata but contains no playback component and no call to `stream-authorizations/playback`.
- Stream Gateway: FastAPI verifies scoped tokens for metadata/status/start/stop routes. Its camera manager loads all enabled cameras from `/api/cameras/internal/all` using an internal token.
- FFmpeg: reads camera RTSP URLs for AI JPEG extraction and rolling segment files. It does not publish output to MediaMTX.
- MediaMTX: declared in both Compose files and started for the synthetic fixture path. No checked-in MediaMTX configuration or authorization hook is present.
- WHEP/HLS: gateway returns `/webrtc/{camera}/whep` and `/hls/{camera}/index.m3u8`, but the gateway has no such routes and no verified MediaMTX handoff/authentication.
- Browser: no source path consumes the authorization result or performs real WHEP/HLS playback.

## Implemented Changes

Only focused validation coverage and documentation were added:

- Extended `apps/stream-gateway/tests/test_stream_gateway.py` to reject cross-site and wrong-camera scopes.
- Added `GAATHACORE_SENTIRA_PLAYBACK_AUTHORIZATION_ASSESSMENT.md`.
- Added this report.
- No MediaMTX, WebRTC, HLS, frontend, Core, PostPilot, Suite, POS, billing, Groq, Gmail, production, DNS, Nginx, or database changes were made.

## Authorization Contract

The scoped token contains camera ID, organization ID, site ID, authenticated user subject, operation, issuer `sentira-api`, audience `sentira-stream-gateway`, 60-second expiry, unique token ID, and request ID. Organization and site are derived from server-side rows; caller-supplied organization/site headers are not trusted. Invalid, expired, wrong-operation, wrong-camera, cross-site, and cross-organization scopes fail closed at the implemented API/gateway boundary.

The boundary does not extend to MediaMTX or a browser media request. Direct media routes would bypass the API unless a verified MediaMTX auth hook, signed URL mechanism, or authenticated proxy is implemented and tested.

## Camera Loading Review

Loading all organizations’ enabled cameras into one gateway is not necessary and increases tenant-cache leakage, startup scaling, stale ownership, and disable/revocation risk. The current internal route is token-protected and not user-facing, but there is no per-organization caller filter and no fresh ownership check for each media request. A future on-demand lookup by verified camera ID is recommended; it was not added because the actual MediaMTX/proxy media path is absent.

## Replay and Connector Findings

Scoped playback tokens are reusable for their 60-second lifetime. `jti` is not persisted and no replay store exists. This is accepted risk for the current metadata/control boundary and is not sufficient for one-time media authorization.

Connector registration pairing is short-lived and single-use, and registration tokens are hashed at rest. Connector tokens have no persisted expiry, rate limiting/brute-force control, explicit revocation, rotation endpoint, or replay detection. No arbitrary lifecycle behavior was added.

## Validation

Exact successful commands run:

```text
PYTHONPATH=. pytest -q tests/test_stream_gateway.py
cd /workspaces/gaathacore/imported/sentira/sentira-main && npm --workspace apps/api test -- --runInBand src/modules/cameras/stream-authorization.service.spec.ts src/modules/cameras/camera-onboarding.service.spec.ts
npm --workspace apps/api run build
python -m compileall -q apps/stream-gateway
```

Passed:

- Stream Gateway unit tests for playback metadata shape.
- Internal gateway token rejection/acceptance tests.
- Scoped token rejection for missing, invalid, expired, wrong-operation, cross-organization, cross-site, and wrong-camera requests.
- API stream-authorization unit tests for 60-second claims, server-side organization lookup, and missing gateway-secret fail-closed behavior.
- Existing connector onboarding unit tests for expired pairing and cross-organization discovered-camera rejection.

Failed: none in the focused tests.

Command setup failures, not product failures:

- An initial `pytest` invocation also included a TypeScript Jest spec and was rejected by pytest.
- Root-level pytest omitted the Stream Gateway local import path; the corrected `PYTHONPATH=.` invocation passed.

Skipped/not run:

- Docker Compose runtime, MediaMTX, FFmpeg, real RTSP, WHEP negotiation, HLS delivery, and browser playback.
- Two-organization live runtime isolation through actual media routes.
- Disable/revocation against an active media session.
- Connector rate-limit, expiry, rotation, and revocation behavior, because those controls do not exist.
- Production/VPS services and databases, intentionally prohibited.

## Required Future Gate

Before browser playback or Core mapping, implement and verify one supported media authorization design: API-issued camera/tenant-scoped authorization consumed by a real MediaMTX auth hook or a server-side playback proxy, with actual camera publication, WHEP/HLS route checks, fresh disable/revocation behavior, and two-organization runtime tests. Until then, playback authorization is not actually verified.
