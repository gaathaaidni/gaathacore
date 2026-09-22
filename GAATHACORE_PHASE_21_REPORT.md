# GaathaCore Phase 21 — Sentira Integration Readiness & Media Risk Review

**Date:** 2026-09-22  
**Mode:** implementation-first, local-only  
**Status:** **YELLOW — static hardening completed; live media gate remains blocked.**

## Scope and evidence

This phase reviewed the repository's Phase 12–20A reports and the current
Sentira API, Stream Gateway, AI Worker, MediaMTX, camera, and connector
boundaries. No deployment, VPS, DNS, Nginx, production database, production
credential, Core mapping, or unrelated imported product was modified. The
unrelated Suite `auto_signup_test.py` blocker was not touched.

## Implemented

Two small, fail-closed `CameraStreamManager` hardening changes were made:

1. A malformed camera projection now causes discovery to treat the projection
   as empty and stop/remove managed streams, rather than allowing a discovery
   task exception to leave a stale publication running.
2. A changed `streamUrl` is now reconciled like an organization/site identity
   change: the existing manager task/publication is stopped before a replacement
   stream starts with the new source.

Focused regression coverage was added for both cases. Changed application files:

* `imported/sentira/sentira-main/apps/stream-gateway/camera_manager.py`
* `imported/sentira/sentira-main/apps/stream-gateway/tests/test_phase7_reliability.py`

This phase also adds this report and the accompanying risk register:

* `GAATHACORE_PHASE_21_REPORT.md`
* `GAATHACORE_SENTIRA_INTEGRATION_RISK_REGISTER.md`

## Verified

Static source review confirms these existing authorization boundaries:

* Native API user authorization is organization scoped. Camera list/get and
  stream-authorization issuance query camera ownership with the authenticated
  user's organization; the stream authorization service also verifies the
  camera's site belongs to that organization.
* The API issues short-lived playback/status/start/stop JWTs with issuer,
  audience, subject, `jti`, organization, site, camera, and operation claims.
* Gateway scoped authorization checks issuer/audience/signature/expiry plus
  camera, organization, site, operation, subject, and `jti` against cached
  camera projection data. The MediaMTX callback re-checks the current camera
  projection, enabled state, organization, and site before allowing a read.
* Media paths are generated from trusted organization/site/camera identifiers;
  the callback parses the path and compares each element to the token and current
  projection instead of treating a path as authorization.
* Internal camera requests require the configured internal token. The internal
  projection contains only ID/organization/site/stream URL/enabled fields, not
  username, encrypted password, or decrypted password.
* AI Worker frame ingestion requires a distinct `X-AI-Worker-Token`, validates
  tenant/frame identifiers and encoded JPEG bounds, and receives no camera
  credential field from the manager.
* Public camera responses remove `streamUrl`, `username`, and
  `passwordEncrypted`. Connector command result sanitization removes
  password/token/secret/authorization/credential-like fields.
* The manager keeps its AI JPEG, rolling buffer, and RTSP publication processes
  in a single per-camera cleanup list. Disabled/deleted reconciliation remains
  idempotent, and source changes now stop the old process group before restart.

The focused Stream Gateway suite now contains **21 tests by source count**
(previously 19; two regression tests were added).

## Partially verified

* Static tests cover tenant-path authorization, disabled/deleted reconciliation,
  three-child cleanup, credential-free command construction, and the two new
  stale-projection/source-change cases. The actual focused test run is blocked
  by missing Python dependencies, so these are source-reviewed rather than
  executed results in this workspace.
* The configured reconciliation delay is five seconds by default. Fresh media
  authorization re-checks current camera state, but the manager's stop action
  occurs only after a successful reconciliation cycle.
* Connector authentication compares a supplied registration token to a stored
  hash and derives organization ownership from the connector record. Its full
  lifecycle security controls remain incomplete; see the risk register.

## Not verified

The following remain explicitly unresolved and must not be inferred from unit
tests or static inspection:

* Two simultaneous manager-produced streams into MediaMTX.
* Live MediaMTX authorization-callback results for both tenant paths, including
  HLS parent/child playlists, init resources, and media segments.
* Browser `/media-test` playback and WHEP SDP negotiation.
* Physical-camera operation.
* Live disable/delete/reassignment lifecycle behavior and orphan-process
  inspection.
* Instant revocation of an already-established HLS session.
* API Jest/build and frontend checks.

## Blocked

Phase 20A established that this workspace has no Docker-compatible container
runtime, FFmpeg, MediaMTX, Sentira Node dependencies, or Stream Gateway Python
dependencies. An isolated Python dependency-install attempt was also blocked by
the configured package proxy returning HTTP 403. No large dependency installation
or replacement runtime was attempted in this phase.

## Security findings

* The hardened malformed-projection behavior is intentionally availability
  conservative: it stops managed streams when the API contract is invalid,
  preventing stale manager state from silently authorizing continued publication.
* Camera credentials remain outside public API results, Stream Gateway
  projections, manager command construction, AI Worker payloads, and these
  reports. The RTSP source URL is a controlled gateway-only field.
* The publication token remains visible in the FFmpeg RTSP target query string.
  It is not a camera password, but this remains a documented operational
  exposure rather than a resolved production control.
* The shared global internal-gateway token and long-lived connector token model
  remain higher-priority design risks; no unsafe caller-supplied tenant input or
  authorization rewrite was introduced.

## Remaining risks

The prioritized, evidence-based register is in
`GAATHACORE_SENTIRA_INTEGRATION_RISK_REGISTER.md`. The most important remaining
risks are the global internal projection credential's blast radius, connector
token lifecycle controls, replay within the short playback-token lifetime,
publication-token process visibility, and the periodic reconciliation delay.

## Test results

| Check | Result |
| --- | --- |
| `python -m py_compile apps/stream-gateway/*.py scripts/phase20a_stub_api.py` | Passed |
| `cd apps/stream-gateway && PYTHONPATH=. python -m pytest -q tests/test_stream_gateway.py tests/test_phase7_reliability.py tests/test_fixture_and_buffer.py` | Blocked: 2 collection errors because `fastapi` and `aiohttp` are unavailable; no focused tests executed |
| `/tmp/gaathacore-phase20a-venv/bin/pip install -r apps/stream-gateway/requirements.txt pytest` | Blocked: configured package proxy returned HTTP 403 |
| `npm --workspace apps/api run test -- --runInBand` | Blocked: `jest` unavailable because API dependencies are absent |
| `npm --workspace apps/web run lint` | Blocked: Next/React/TypeScript dependencies are absent |
| `docker compose -f docker-compose.phase20a.yml config` | Blocked: Docker Compose unavailable |
| Static security inspection with `rg` over camera, Stream Gateway, AI Worker, and connector paths | Completed; findings recorded above and in the risk register |
| `git diff --check` | Passed |

## Recommended next phase

Keep Sentira **YELLOW**. First restore a disposable local Docker-compatible
environment and complete the existing Phase 20A two-manager MediaMTX/HLS gate,
recording real callback statuses and lifecycle/process evidence. In parallel or
subsequently, approve a least-privilege replacement for the global internal
projection token and define connector credential lifecycle controls. Do not
start Core mapping before those boundaries and the live media gate are resolved.
