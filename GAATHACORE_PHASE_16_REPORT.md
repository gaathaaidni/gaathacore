# GAATHACORE PHASE 16 REPORT

Date: 2026-09-22
Scope: Sentira only
Status: LOCAL MEDIA CAPABILITY PROVEN; AUTHENTICATED BROWSER PLAYBACK BLOCKED

## Result

Phase 16 proved the local synthetic media capability only:

```text
FFmpeg fixture -> RTSP -> MediaMTX v1.21.1 -> HLS parent playlist (HTTP 200)
```

The real-camera publication path is still absent. WHEP was not negotiated with valid SDP. The Next.js frontend still has no playback consumer. The Sentira playback authorization token still does not reach the actual MediaMTX media request. Core mapping remains blocked and production readiness is not claimed.

## Actual Architecture Discovered

### Real camera

`CameraStreamManager` fetches all cameras through the internal API route, then starts FFmpeg to read each camera `streamUrl`. One process extracts MJPEG frames for the AI worker and one writes rolling segments. There is no FFmpeg output aimed at MediaMTX and no camera-to-MediaMTX path registration. Real camera RTSP-to-MediaMTX is UNIMPLEMENTED.

### Synthetic fixture

`fixture_publisher.py` uses FFmpeg `testsrc2` and `sine` inputs and publishes RTSP to `rtsp://<host>:8554/<path>`. With the existing Stream Gateway image and a local MediaMTX container, logs showed an online `fixture` path with H.264 and MPEG-4 Audio tracks. MediaMTX created an HLS muxer and returned a parent playlist with `Content-Type: application/vnd.apple.mpegurl` and HTTP 200. This path is IMPLEMENTED and locally verified.

### AI worker

The gateway posts extracted JPEG frames to `AI_WORKER_URL/frames` with `X-AI-Worker-Token` and organization/site/camera fields. The source path is IMPLEMENTED, but the full Docker-backed AI flow was not run in this phase.

### Browser

The dashboard loads camera metadata and status but does not call `/stream-authorizations/playback`, `/streams/{camera}/playback`, HLS, or WHEP. Browser playback is UNIMPLEMENTED.

## MediaMTX Verification

- Repository image declaration: `bluenviron/mediamtx:latest` in both Compose files.
- Exact local image result: MediaMTX `v1.21.1`, Linux amd64.
- Shipped config: RTSP `:8554`, HLS `:8888`, WebRTC HTTP/WHEP `:8889`; internal auth, external HTTP auth, JWT/JWKS auth, path permissions, HLS CDN secret, and path source types are documented in the image configuration.
- Sentira Compose local exposure: RTSP `8554` and WebRTC port `8889`; HLS port `8888` is not exposed.
- Sentira configuration: no checked-in MediaMTX config, external HTTP callback, JWT/JWKS configuration, signed URL integration, WHEP handler, or HLS handler.

Actual request results:

- RTSP fixture publication: PASS. MediaMTX logged `stream is available and online` on `fixture` with H.264/AAC tracks.
- HLS parent playlist: PASS. `GET /fixture/index.m3u8?cookieCheck=1` with the local session cookie returned HTTP 200 and an HLS playlist.
- HLS child/segment: NOT PROVEN. A subsequent child request returned `401 session not found`; the complete MediaMTX HLS session/cookie exchange was not implemented or reproduced as a browser player.
- WHEP route: PASS as route existence only. An empty SDP POST returned HTTP 400; valid WebRTC SDP negotiation was NOT RUN.
- Sentira playback metadata: remains metadata only and points to routes not served by the Stream Gateway.

## Authorization Result

The API issues 60-second HS256 tokens containing camera ID, organization ID, site ID, authenticated user, `playback` operation, issuer `sentira-api`, audience `sentira-stream-gateway`, expiry, JTI, and request ID. The gateway validates those tokens for its metadata/control routes. No MediaMTX request consumed that token, and no browser request was authorized through it.

Therefore:

- API authorization: IMPLEMENTED and unit tested.
- Gateway metadata authorization: IMPLEMENTED and unit tested.
- Actual media authorization: UNIMPLEMENTED.
- Unauthorized browser playback rejection: NOT TESTABLE through the current browser path.

## Two-Organization Isolation

The existing `two-tenant.security.spec.ts` was run with its default flag and skipped all five tests. It was then run with `SENTIRA_LIVE_INTEGRATION=1` and all five tests failed immediately because no local API runtime was listening. No API, database, or full Compose stack was started.

The gateway/API unit tests cover cross-organization, cross-site, wrong-camera, wrong-operation, and expired scoped tokens at the implemented metadata boundary. They do not prove A-token-to-B-media or B-token-to-A-media rejection because no Sentira-authorized media path exists.

Two-organization media result: NOT PROVEN.

## Disable, Reassignment, Membership, and Expiry

- New authorization after camera disable: the API service currently queries organization/camera ownership but does not reject `isEnabled: false`; this behavior is not a supported revocation guarantee.
- Existing gateway cache after disable/reassignment: stale in-memory camera ownership can remain accepted for metadata/control requests.
- Existing MediaMTX sessions: no Sentira session or revocation integration exists; active-session revocation is NOT IMPLEMENTED.
- User membership removal: not connected to an existing scoped playback token after issuance.
- Token expiry: API/gateway JWT validation rejects expired tokens at the gateway boundary; no real MediaMTX request was tested with one.

## Security Review

- All-camera gateway cache: present, cross-tenant metadata is loaded into one process, and startup/process scaling is global. This increases stale ownership and disablement risk.
- Camera URL exposure: public API responses redact stream URL, username, and encrypted password. The internal gateway response is protected by `X-Internal-Token`, but it returns all organizations’ stream URLs.
- MediaMTX direct exposure: local Compose exposes RTSP and WebRTC ports; HLS is not exposed. Production Compose keeps MediaMTX internal. No Sentira authorization protects direct MediaMTX access.
- Predictable media paths: fixture and metadata paths use camera/path identifiers. UUIDs are not the security boundary.
- Authorization bypass: direct MediaMTX paths would bypass Sentira because no callback, JWT/JWKS setup, signed URL, or proxy is configured.
- Replay: scoped tokens are reusable for 60 seconds; JTI is not stored. No nonce store was added.
- Connector security: Phase 15 findings remain: pairing is short-lived and single-use, registration tokens are hashed, but connector-token expiry, rate limiting, revocation, rotation, and replay detection are absent. No unrelated connector lifecycle changes were made.

## Exact Files Changed

- `GAATHACORE_SENTIRA_MEDIA_PIPELINE_DESIGN.md`
- `GAATHACORE_PHASE_16_REPORT.md`

No Sentira source, Compose, frontend, MediaMTX configuration, Core, Suite, POS, PostPilot, production, DNS, Nginx, or database files were changed.

## Exact Commands and Results

Capability inspection and disposable runtime:

```text
docker pull bluenviron/mediamtx:latest                         PASS
docker run --rm bluenviron/mediamtx:latest --version           PASS: v1.21.1
docker run --rm bluenviron/mediamtx:latest --help              PASS
docker build -t phase16-sentira-stream-gateway ./imported/sentira/sentira-main/apps/stream-gateway  PASS
```

The disposable runtime used the existing gateway image’s fixture publisher and a temporary host-networked MediaMTX container. It was removed after validation. The successful probe requested the HLS parent URL and posted an empty SDP to the WHEP URL; the detailed command output and statuses are recorded above.

Repository validation:

```text
cd imported/sentira/sentira-main/apps/stream-gateway && PYTHONPATH=. pytest -q tests/test_stream_gateway.py tests/test_fixture_and_buffer.py tests/test_phase7_reliability.py  PASS: 9 passed
cd imported/sentira/sentira-main && npm --workspace apps/api test -- --runInBand src/modules/cameras/stream-authorization.service.spec.ts src/modules/cameras/camera-onboarding.service.spec.ts  PASS: 7 passed
npm --workspace apps/api run build  PASS
npm --workspace apps/web run build  PASS with existing <img> lint warnings
cd imported/sentira/sentira-main && npm --workspace apps/api run test:integration  SKIPPED: live flag disabled
cd imported/sentira/sentira-main && SENTIRA_LIVE_INTEGRATION=1 npm --workspace apps/api run test:integration  FAILED/BLOCKED: no local API runtime listening
```

Not run or blocked:

- Full Compose startup, API/database/AI-worker runtime, and physical camera path: NOT RUN.
- Valid WHEP SDP/browser negotiation: NOT RUN.
- Frontend playback tests: none exist.
- Two-organization actual media isolation: BLOCKED by absent authorized media path and unavailable local API runtime.
- Active-session disable/revocation: NOT IMPLEMENTED.

## Stop Condition

The local media capability is sufficient to justify a future MediaMTX-backed implementation, but the repository evidence is insufficient to choose and safely connect an authorization mechanism. Phase 16 stops here. Sentira-to-Core mapping must not begin.
