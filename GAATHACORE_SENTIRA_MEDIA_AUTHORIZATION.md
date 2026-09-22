# Sentira Media Authorization Boundary

**Phase 18 status: YELLOW**

This is a local/Codespace implementation and proof only. No deployment, VPS,
production Compose, DNS, Nginx, TLS, firewall, production database, Core
mapping, or real camera was used.

## Selected mechanism

Sentira uses MediaMTX v1.21.1 `authMethod: http` with an external HTTP
callback at the Stream Gateway. This is one authorization mechanism. It was
selected because MediaMTX v1.21.1 sends every HLS/WHEP read request to the
callback, accepts the existing Sentira HS256 bearer token, and does not require
introducing a JWKS key-distribution service or a second token format.

The local configuration is [mediamtx.yml](imported/sentira/sentira-main/mediamtx.yml).
The production Compose file remains unchanged and production readiness is not
claimed.

## Request flow and boundary

1. Native Sentira JWT authentication and `camera.view` permission protect the
   API playback-authorization endpoint.
2. Sentira looks up the camera by the authenticated user's organization and its
   site, and now rejects disabled cameras before issuing a token.
3. The API issues a 60-second HS256 token with `iss`, `aud`, `sub`, `jti`,
   `organizationId`, `siteId`, `cameraId`, `operation: playback`, `iat`, `exp`,
   and `requestId` claims. The signing secret is not exposed in this report.
4. A client sends `Authorization: Bearer <token>` to the actual MediaMTX HLS
   or WHEP endpoint.
5. MediaMTX POSTs `{action, path, protocol, token, ...}` to
   `/media/auth`. The gateway verifies the JWT, requires playback/read scope,
   derives the tenant/site/camera from the path, and compares every value with
   the token.
6. The gateway performs a fresh internal API camera lookup for every media
   read authorization and requires the camera to be enabled with the same
   organization and site. MediaMTX allows the request only on a 2xx response.

The path is an identifier, not the security boundary. Changing only the path
without a matching token is rejected.

## Media results

- HLS selected and proven with actual media requests. The parent playlist,
  child playlist, and an fMP4 init segment each returned HTTP 200 with bearer
  authorization and the MediaMTX session cookie flow.
- Organization A to Camera A: HTTP 200 playlist/child/segment.
- Organization B to Camera B: HTTP 200 playlist in the live probe.
- A token to B path: rejected by MediaMTX; callback returned 403 scope mismatch.
- B token to A path: covered by callback tests and the same path-scope logic.
- Missing authorization: MediaMTX returned HTTP 401.
- Invalid/expired authorization: MediaMTX returned HTTP 401.
- Path enumeration/wrong path: rejected by callback with 401/403; the path is
  not trusted by itself.
- The HLS request requires the bearer header on the parent and child/segment
  requests, plus the MediaMTX `cookieCheck` and session-secret cookie exchange.
  Native browser playback was not verified.
- WHEP route/auth capability was inspected, but a valid SDP offer and actual
  WHEP negotiation were not generated. WHEP is **NOT VERIFIED**.
- Browser playback is **NOT VERIFIED**. `/media-test` remains a local fixture
  page and is not claimed as secure browser playback.

## Lifecycle, replay, and revocation

The callback is stateless. A valid token can be replayed during its 60-second
lifetime; `jti` is validated for presence but is not stored. This is an
accepted local limitation, not one-time authorization.

Fresh media requests after disabling the camera were rejected by MediaMTX
(HTTP 401, caused by the callback's current-state denial). Fresh requests after
reassignment to another organization/site were also rejected. A previously
created HLS session is not forcibly terminated by this implementation; active
session revocation is therefore not instant. User suspension or permission
loss after token issuance has the same limitation unless the fresh camera/API
check denies the request. Token expiry is enforced by JWT validation.

## Camera credentials and real cameras

No camera credentials are sent to the browser, HLS URL, WHEP URL, frontend, or
Core. Existing camera passwords remain encrypted at rest. The internal camera
projection used by the gateway contains no username/password and the current
CameraStreamManager does not decrypt credentials. Real-camera MediaMTX
publication was not added because its credentialed source path is not yet
connected to this boundary. Existing AI JPEG, rolling MP4, reconnect, and
supervision behavior was not changed.

## Tests and probes

Passed:

- Stream Gateway focused and fixture tests: **10 passed**.
- Python compilation: **passed**.
- MediaMTX v1.21.1 config validation: **passed**.
- Live HLS parent/child/init-segment probe: **200/200/200** for A.
- Live HLS parent probe: **200** for B.
- Live unauthenticated probe: **401**.
- Live cross-path and expired-token probes: **401/403** at MediaMTX/callback.
- Live disabled and reassigned fresh-request probes: **401** at MediaMTX.
- `git diff --check`: **passed**.
- Editor diagnostics for changed Python and TypeScript files: **no errors**.

Not executed because this checkout lacks installed dependencies:

- API Jest tests: Jest unavailable (`jest: not found`).
- Frontend build: not run; web dependencies are not installed.
- Full API/integration suite: not run.
- Valid WHEP SDP negotiation: not verified.
- Browser playback: not verified.
- Real-camera publication: not implemented or tested.

## Remaining blockers

- WHEP valid SDP negotiation remains unverified.
- Browser playback remains unverified.
- Replay within token lifetime is possible.
- Existing HLS/WHEP sessions do not receive instant revocation.
- Real-camera publication and its server-side credentialed source path remain
  unimplemented.
- Production MediaMTX deployment configuration was intentionally not changed;
  this phase proves only the local boundary.

Secure playback is **not locally proven for all protocols or browser playback**.
The final Phase 18 status is **YELLOW**, not production readiness.
