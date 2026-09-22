# GaathaCore Sentira Stream Security Assessment

**Assessment date:** 2026-09-22  
**Phase:** 14 - Sentira Tenant-Aware Stream and Camera Credential Boundary  
**Scope:** local source inspection and focused local validation only

## Decision

Phase 14 reduced credential exposure at the API-to-gateway boundary, but did not implement tenant-aware gateway control or MediaMTX/WebRTC authorization. The existing architecture starts the gateway by loading all enabled cameras, and its control token carries no organization, site, user, operation, or correlation scope. A tenant-aware redesign would require a new service contract and an API authorization path that do not exist locally.

**Status: YELLOW. Production readiness remains NOT READY.**

## Actual camera flow

1. An authenticated Sentira user creates a camera through `POST /api/cameras`.
2. The API validates the stream URL, rejects embedded URL credentials and private network targets for manual cameras, verifies `siteId` belongs to the authenticated organization, encrypts a supplied password, and persists the camera in the independent Sentira database.
3. Public camera responses remove `passwordEncrypted`, `streamUrl`, and `username`.
4. On startup, the Stream Gateway sends `X-Internal-Token` to `/api/cameras/internal/all`.
5. The API validates the shared service token. It now returns only selected stream fields: camera ID, organization ID, site ID, stream URL, and enabled state. It does not select, decrypt, or return camera credential fields.
6. The gateway caches every returned camera by camera ID and starts enabled cameras automatically.
7. Start, stop, playback metadata, and status endpoints accept the same shared gateway token and a camera ID. The gateway checks only whether the camera ID exists in its cache; it does not validate organization or site scope.
8. FFmpeg reads `streamUrl` directly. The current gateway does not use username or password fields, and MediaMTX is not in the FFmpeg input/output path.
9. The gateway sends sampled JPEG frames to the AI Worker with a separate worker token. The API later validates the detection organization's camera/site relationship before event processing.
10. Playback metadata advertises `/webrtc/{cameraId}/whep` and `/hls/{cameraId}/index.m3u8`, but those routes are not implemented by the gateway and no API playback proxy or MediaMTX authorization hook exists.

## Scope-loss points

- The API-to-gateway configuration request authenticates the service but has no requested organization or camera scope.
- The response historically loaded all camera rows and decrypted all passwords; this phase removes the credential fields but retains the all-camera startup contract.
- Gateway control requests carry only a camera ID and shared token. A caller cannot prove organization, site, permitted operation, or user delegation.
- Camera ownership is not re-queried by the gateway for control operations.
- MediaMTX URLs are not generated from an authorization decision and camera identifiers are predictable.
- Camera credentials are stored encrypted in Sentira, but the active gateway path does not consume them, so authenticated external camera credential support is incomplete rather than safely delegated.

## Implemented changes

### Internal camera configuration minimization

`CamerasService.findAllInternal()` now uses a TypeORM projection and returns only fields currently consumed by `CameraStreamManager`: `id`, `organizationId`, `siteId`, `streamUrl`, and `isEnabled`. It no longer returns `passwordEncrypted`, `password`, `username`, or unrelated ORM fields, and it no longer decrypts credentials.

The existing shared service token remains required. The endpoint is still all-tenant and therefore is not yet a tenant-aware retrieval contract.

### Configuration propagation

The production Compose template now requires `AI_WORKER_INGEST_TOKEN` for both AI Worker and Stream Gateway. No credential value was added. This preserves the Phase 13 fail-closed worker boundary in the production template without deploying or changing production secrets.

## Gateway control decision

Tenant-aware control was **not implemented**. The current protocol lacks:

- an authenticated caller identity distinct from the shared service token;
- an organization/site/camera scope assertion that the API can verify;
- an API endpoint for the gateway to authorize a specific operation;
- a lifecycle for short-lived, operation-specific control tokens;
- a defined mapping between browser/user playback requests and gateway operations.

Adding organization headers or trusting caller-supplied organization IDs would not be a security improvement. The required next design is an API-authorized, short-lived, camera-specific operation contract, followed by gateway-side validation and two-organization tests.

## Media authorization decision

Media authorization remains **blocked/design-only**:

- MediaMTX is declared in Compose, but no custom configuration, stream publication path, WHEP authorization hook, HLS authorization hook, or signed URL mechanism is present.
- The gateway returns predictable camera-ID-based playback URLs without a verified authorization step.
- No browser-facing API endpoint was found that authenticates the user and authorizes playback against organization/site/camera ownership.
- No tenant-safe playback claim is made.

## Connector token review

Implemented controls:

- Pairing codes are random, hashed, single-use, and expire after ten minutes.
- Connector registration tokens are 32 random bytes and only their SHA-256 hashes are persisted.
- Connector revoke clears the stored token hash and disables the connector.
- Connector rotation replaces the hash and returns a new token once.
- Connector operations derive organization ownership from the stored connector, and command/result queries constrain connector and organization IDs.
- Connector tokens and camera secrets are not intentionally logged.

Unresolved controls:

- Registration tokens have no stored expiry; they remain valid until rotation or revocation.
- No rate limiting or brute-force protection exists at the controller/service layer.
- Replay resistance is limited to command state, expiration, idempotency, and connector ownership; token reuse itself is not one-time.
- Connector HTTP endpoints are unauthenticated by JWT by design, so deployment network isolation and rate limiting remain required.

These are documented rather than changed because token expiry and rate-limit semantics require a connector lifecycle decision.

## Security tests and evidence

- Camera service test proves the internal projection contains no encrypted/decrypted credential fields and does not call decryption.
- Existing API tests prove separate organization IDs cannot retrieve another organization's camera, event, evidence, or storage namespace.
- Existing worker/API tests reject missing or mismatched tenant metadata before detection processing.
- Gateway tests prove missing and invalid shared credentials fail and valid configured credentials pass.
- Cross-organization gateway control is not proven because the current gateway request has no tenant scope; this is an explicit unresolved risk.

## Configuration and database impact

- No database schema, migration, database URL, cross-database join, or foreign key changed.
- Sentira remains independent from `gaathacore_core`.
- The internal projection removes credential selection from the API query; no data migration is required.
- `AI_WORKER_INGEST_TOKEN` is required in the production Compose template and must be supplied by the deployment environment. No secret value was added.

## VPS and production impact

- VPS access: none.
- Deployment or service restart: none.
- DNS/Nginx: unchanged.
- Production database and credentials: unchanged.
- Production readiness: not ready.

## Core mapping decision

Core mapping remains prohibited. No Sentira-to-Core adapter, synchronization, identity mapping, or Core module access write was implemented. Mapping can begin only after tenant-aware gateway control and playback authorization have an approved contract and passing two-organization tests.
