# GAATHACORE PHASE 18 REPORT

**Date:** 2026-09-22  
**Scope:** Sentira only  
**Final status:** **YELLOW: actual HLS media authorization and tenant isolation
are proven locally; WHEP, browser playback, revocation of active sessions, and
real-camera publication remain unverified.**

## Executive result

Implemented one real MediaMTX authorization boundary:

```text
Sentira native auth and camera permission
  -> 60-second camera/org/site playback JWT
  -> MediaMTX Authorization bearer request
  -> MediaMTX v1.21.1 external HTTP auth callback
  -> fresh Sentira camera state lookup
  -> HLS media session, child playlist, and fMP4 segment
```

The synthetic fixture was published into separate paths for Organization A and
B. Actual MediaMTX HLS requests proved authorized access and cross-organization
rejection. No Core mapping was started.

## Implementation

Changed Sentira files:

- `imported/sentira/sentira-main/apps/api/src/modules/cameras/cameras.service.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/cameras.controller.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/stream-authorization.service.ts`
- `imported/sentira/sentira-main/apps/api/src/modules/cameras/stream-authorization.service.spec.ts`
- `imported/sentira/sentira-main/apps/stream-gateway/config.py`
- `imported/sentira/sentira-main/apps/stream-gateway/fixture_publisher.py`
- `imported/sentira/sentira-main/apps/stream-gateway/main.py`
- `imported/sentira/sentira-main/apps/stream-gateway/media_paths.py`
- `imported/sentira/sentira-main/apps/stream-gateway/tests/test_stream_gateway.py`
- `imported/sentira/sentira-main/docker-compose.yml`
- `imported/sentira/sentira-main/mediamtx.yml`
- `GAATHACORE_SENTIRA_MEDIA_AUTHORIZATION.md`
- `GAATHACORE_PHASE_18_REPORT.md`

The local Compose file mounts the checked-in MediaMTX config and keeps the
callback on the private service network. Production Compose was not modified.

## Required findings

1. **Mechanism:** MediaMTX v1.21.1 external HTTP authentication callback.
2. **Why:** It accepts the existing bearer JWT on HLS/WHEP requests and lets
   Sentira perform authoritative state checks for every request.
3. **Exact boundary:** MediaMTX receives the token-bearing request and denies
   non-2xx callback responses. The media path is only an identifier.
4. **Claims:** issuer `sentira-api`, audience `sentira-stream-gateway`, user
   subject, JTI, organization ID, site ID, camera ID, `playback` operation,
   issued-at, expiry, and request ID. No secret values are reported.
5. **HLS:** Proven through the parent playlist, child playlist, and fMP4 init
   segment. The `Authorization` header is required; MediaMTX also uses its
   `cookieCheck` and session-secret cookie for subsequent HLS requests.
6. **WHEP:** MediaMTX callback support was inspected, but valid SDP negotiation
   was not generated. **NOT VERIFIED.**
7. **Browser:** **NOT VERIFIED.** The existing `/media-test` page is not used
   as authorization proof.
8. **Tenant isolation:** A->A and B->B succeeded; A->B and B->A scope mismatch
   requests were rejected. Changing only the path did not bypass authorization.
9. **Disabled/reassigned:** Fresh requests after disable and reassignment were
   rejected by the callback through MediaMTX. API issuance also rejects disabled
   cameras.
10. **Replay:** A valid JWT can be replayed within its 60-second lifetime;
    JTI is not persisted.
11. **Revocation:** Fresh requests re-check current camera state. Existing HLS
    sessions are not forcibly revoked; instant revocation is not claimed.
12. **Direct access:** Unauthenticated direct HLS access returned 401. MediaMTX
    is configured to call Sentira for read requests.
13. **Credentials:** Camera credentials remain server-side/encrypted. No real
    camera publication was added and no source credentials reached media URLs.
14. **Real camera:** Not implemented in this phase; existing AI JPEG and rolling
    MP4 manager behavior was preserved.

## Exact validation

- Stream Gateway and fixture tests: **10 passed**.
- Python compilation: **passed**.
- MediaMTX v1.21.1 `--validate-conf`: **passed**.
- Actual HLS A parent/child/segment: **200/200/200**.
- Actual HLS B parent: **200**.
- Unauthenticated media request: **401**.
- Invalid/expired media authorization: **401**.
- Cross-organization/path mismatch: **403** callback decision, surfaced as
  MediaMTX rejection.
- Disabled/reassigned fresh media request: **401** surfaced by MediaMTX.
- `git diff --check`: **passed**.
- Changed-file editor diagnostics: **no errors**.

Skipped or unavailable:

- API Jest tests: dependency unavailable (`jest: not found`).
- Frontend build: dependencies unavailable and browser playback not verified.
- Valid WHEP SDP negotiation.
- Real-camera MediaMTX publication.
- Full Compose/API/database integration.

## Stop condition and blockers

Do not proceed to Core/Sentira organization mapping from this phase. Review is
required before any next phase. This is not production readiness.

Remaining blockers are valid SDP WHEP proof, browser playback proof, active
session revocation, replay prevention, and safe real-camera publication. Final
status remains **YELLOW**.
