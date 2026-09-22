# GaathaCore Sentira Playback Authorization Assessment

Date: 2026-09-22

## Result

Sentira does **not** currently have verified browser playback authorization. The API and Stream Gateway authorize a playback-metadata request, but the returned WHEP and HLS paths are not implemented by the Stream Gateway, are not connected to a verified MediaMTX authorization hook or proxy, and are not consumed by the Next.js frontend. No production playback behavior was changed.

Core mapping remains blocked.

## Actual Runtime Path

1. The API stores a credential-free `streamUrl` and encrypts an optional camera password. User camera reads redact `streamUrl`, username, and password material.
2. `CameraStreamManager` calls the API internal all-camera endpoint with `X-Internal-Token`, loads every organization’s enabled camera into one in-memory process, and starts one supervised FFmpeg pair per camera. One FFmpeg process extracts MJPEG frames for the AI worker; the other writes rolling segments. It does not publish a stream to MediaMTX.
3. Compose starts MediaMTX and a synthetic fixture publisher. The fixture publishes to MediaMTX only for its own test path. No camera-manager code publishes camera output to MediaMTX.
4. `GET /streams/{camera_id}/playback` returns relative metadata paths: `/webrtc/{camera_id}/whep` and `/hls/{camera_id}/index.m3u8`. The Stream Gateway has no routes for either path.
5. The Next.js source has no playback component or call to the API stream-authorization endpoint. Therefore no browser path consumes the scoped authorization result.
6. Compose exposes MediaMTX RTSP port `8554` and port `8889`, but has no checked-in MediaMTX configuration, WHEP/HLS auth hook, or gateway proxy route. The actual browser media negotiation path was not verified.

## Authorization Boundary

The supported boundary is:

- `POST /api/cameras/:id/stream-authorizations/playback` requires the native Sentira JWT and `camera.view` permission.
- The API looks up the camera by `id` and authenticated `organizationId`, then verifies the camera’s site belongs to that organization.
- It issues an HS256 token with camera ID, organization ID, site ID, authenticated user ID, `operation`, issuer `sentira-api`, audience `sentira-stream-gateway`, `exp` 60 seconds after issuance, `jti`, and a request/correlation ID.
- Stream Gateway verifies signature, issuer, audience, expiry, subject, JTI, operation, camera ID, and the cached camera organization/site pair.

This protects the metadata/control endpoints only. It does not protect the WHEP or HLS media paths because those paths are not served or authorization-bound in the current runtime. A direct MediaMTX path, if configured externally, would bypass this API authorization service.

Camera IDs are UUIDs and not practically guessable, but predictability is not the security boundary. Organization, site, camera, operation, and permission checks are required for every authorization request.

## Safe Playback Contract

The intended contract is camera-specific and server-derived:

| Field | Requirement |
| --- | --- |
| camera ID | Authenticated API path parameter; must belong to the authenticated organization and requested site relation |
| organization ID | Derived from the verified Sentira JWT and camera row; caller headers are ignored |
| site ID | Derived from the camera row and verified against the organization |
| authenticated user | Verified Sentira JWT subject and permission set |
| operation | Fixed enum; playback is distinct from status, start, and stop |
| issuer | `sentira-api` |
| audience | `sentira-stream-gateway` |
| expiry | 60 seconds |
| token ID | Unique `jti` |
| replay policy | Reusable during token lifetime; no nonce store or one-time enforcement exists |
| failure behavior | API rejects missing/cross-tenant camera with not-found semantics; gateway rejects invalid tokens with 401 and scope mismatch with 403/404 |
| target service | Stream Gateway authorization endpoint only; no verified MediaMTX target exists |
| request ID | Optional `X-Request-Id`, otherwise generated and included as `requestId` |

Organization and site headers must never be trusted. The current API contract follows that rule.

## Gateway Camera Loading Review

The current all-organization startup load is unnecessary and creates operational risk:

- It places every tenant’s camera metadata and stream source in one gateway cache.
- Startup work and FFmpeg process count scale with the entire deployment, not active viewers or authorized tenants.
- Cached ownership and `isEnabled` state can become stale after reassignment or disablement.
- The internal response is not user-facing and does not return encrypted password material, but the gateway still receives all organizations’ source URLs.

An on-demand, server-to-server camera lookup keyed by the already verified camera ID, with bounded per-camera caching and explicit disable/revocation refresh, is the safer future design. It must be paired with a real MediaMTX/proxy authorization path before browser playback is enabled. No unsafe caller-supplied organization filter was added.

## Replay Policy

The 60-second scoped token is reusable. `jti` is present for correlation and future replay controls, but it is not stored or checked. Request IDs do not make a token one-time. A shared nonce store would add availability, eviction, clock, and failure-mode requirements and was not introduced without existing infrastructure and an operational design.

## Connector Security Review

Connector registration uses a short-lived, single-use onboarding session and stores only a SHA-256 registration-token hash. Heartbeat and discovery compare the presented token hash and scope the resulting data to the connector’s organization. The token is returned at registration/pairing time only.

Remaining gaps are material: connector registration tokens have no persisted expiry, explicit revocation or rotation endpoint, brute-force/rate-limit control, attempt telemetry, or replay detection. `usedAt` protects the onboarding pairing code, not later connector-token reuse. These lifecycle changes require an explicit connector protocol and operational policy, so they were not invented in this phase.

## Security Conclusion

The API-to-gateway metadata authorization checks are locally testable and camera/organization/site/operation scoped. Live tenant isolation for browser playback is **not verified** because the browser-to-media runtime path is absent. Unauthorized, expired, cross-organization, cross-site, wrong-camera, and wrong-operation requests are rejected at the implemented authorization boundary, but cannot be claimed for a real WHEP/HLS media request.
