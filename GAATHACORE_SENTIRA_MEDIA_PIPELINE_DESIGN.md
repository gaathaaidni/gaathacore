# GaathaCore Sentira Media Pipeline Design

Date: 2026-09-22
Scope: Sentira only
Status: Architecture comparison only; no speculative media authorization was implemented.

## Evidence Boundary

The repository declares `bluenviron/mediamtx:latest`. The locally pulled image reports MediaMTX `v1.21.1`. Its shipped configuration documents RTSP publishing, HLS, WebRTC/WHEP, path matching, internal permissions, external HTTP authentication, and JWT/JWKS authentication. Sentira does not check in a MediaMTX configuration and does not configure any of those authorization mechanisms.

The existing synthetic fixture was proven locally to publish FFmpeg-generated H.264/AAC over RTSP to MediaMTX and to produce a `200 OK` HLS parent playlist. A valid WHEP SDP exchange was not performed. This proves MediaMTX capability and the fixture path, not Sentira browser authorization.

## Current Flow

### A. Real camera flow

```text
camera RTSP source
  -> API camera row
  -> Stream Gateway internal all-camera fetch
  -> FFmpeg input in CameraStreamManager
       -> JPEG frames -> AI Worker /frames
       -> FFmpeg segments -> rolling buffer
  -X-> MediaMTX publication
```

- API-to-gateway authentication: `X-Internal-Token`; IMPLEMENTED in source.
- Tenant context: organization/site/camera fields come from the API row; IMPLEMENTED in source, not live verified here.
- Camera credentials: embedded URL credentials are rejected; encrypted password storage exists, but the internal camera response does not provide decrypted credentials to the manager. Credentialed real-camera ingestion is therefore not proven.
- MediaMTX publication: UNIMPLEMENTED for real cameras.
- WHEP/HLS from this path: UNIMPLEMENTED.

### B. Synthetic fixture flow

```text
fixture_publisher.py / FFmpeg testsrc2 + sine
  -> RTSP publish to MediaMTX :8554/fixture
  -> MediaMTX HLS :8888/fixture/index.m3u8
  -> MediaMTX WebRTC/WHEP :8889/fixture/whep
```

- Fixture source: IMPLEMENTED.
- RTSP publication: IMPLEMENTED and locally verified.
- HLS parent playlist: IMPLEMENTED and locally verified with HTTP 200.
- HLS child/segment retrieval: not fully verified; a follow-up child request returned MediaMTX `401 session not found` because the probe did not establish the complete HLS session behavior.
- WHEP route: IMPLEMENTED by MediaMTX; an empty SDP POST returned HTTP 400. Valid SDP negotiation is UNVERIFIED.
- Sentira tenant authorization on this fixture path: UNIMPLEMENTED.

### C. AI-worker flow

```text
Stream Gateway FFmpeg JPEG extraction
  -> POST AI_WORKER_URL/frames with X-AI-Worker-Token
  -> AI Worker processing
  -> downstream detection/event path
```

- Frame authentication: IMPLEMENTED in source.
- organization/site/camera fields: copied from the gateway camera record; IMPLEMENTED in source.
- Docker-backed AI flow: NOT RUN in Phase 16.

### D. Browser playback flow

```text
Next.js dashboard
  -X-> API playback authorization
  -X-> Stream Gateway playback metadata
  -X-> MediaMTX HLS/WHEP request
```

- API scoped authorization endpoint: IMPLEMENTED and unit tested.
- Stream Gateway scoped metadata authorization: IMPLEMENTED and unit tested.
- Frontend playback consumer: UNIMPLEMENTED.
- MediaMTX authorization connected to Sentira token: UNIMPLEMENTED.
- Browser playback: NOT VERIFIED and must not be claimed.

## MediaMTX Capability Comparison

The following options are capabilities evidenced by the local v1.21.1 image. They are not ranked and none was selected for production behavior in this phase.

| Approach | Authentication | Authorization / tenant isolation | Lifetime / replay / revocation | Current FFmpeg | WHEP | HLS | Frontend work | Current status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. MediaMTX external HTTP auth | MediaMTX `authMethod: http` calls `authHTTPAddress` for authentication requests | Callback would need to validate the Sentira token, operation, path, organization, site, and camera mapping; path names alone are not tenant proof | Can enforce expiry if callback validates token claims; replay remains reusable unless callback adds state; new requests can be denied, active sessions need separate behavior | Compatible with publisher output | Compatible with WHEP requests if callback receives and validates them | Compatible with HLS requests if callback receives and validates them | Must obtain scoped authorization and send it on every media request in a MediaMTX-supported form | Not implemented; callback request contract is not present in Sentira |
| B. Server-side playback proxy | Proxy validates the existing Sentira scoped JWT before forwarding media requests | Proxy can derive organization/site/camera from API data and never expose internal MediaMTX directly | Token expiry is straightforward; replay is reusable unless state is added; new requests can be revoked by rechecking API state; active sessions need stream termination support | Compatible if MediaMTX receives the real published path; current gateway does not proxy media | Possible if proxy forwards WHEP signaling correctly | Possible, but proxy must handle playlists, child manifests, segments, cookies, and range behavior | Must request a scoped token and use the proxy URL/session | No proxy exists |
| C. Signed or short-lived media URLs | Requires a MediaMTX or proxy feature that validates a signature/query token | Signature service must bind path to organization/site/camera and operation; caller headers are not sufficient | Expiry can be encoded; replay is normally reusable until expiry; revocation is limited without a deny list | Compatible with media publication | Only if the installed WHEP path accepts the signed form | MediaMTX ships an HLS CDN bearer secret setting, but no evidence here shows per-camera Sentira signed URLs | Must consume the signed URL/session | Not evidenced as a Sentira-compatible mechanism |
| D. MediaMTX JWT/JWKS auth | MediaMTX can use `authMethod: jwt`, a JWKS URL, issuer/audience checks, and `mediamtx_permissions` claims | JWT permissions can bind publish/read/playback to a path; Sentira would need a path naming and claim design that binds tenant and camera | JWT expiry is supported by token validation; replay is reusable until expiry; active revocation requires key/deny-list strategy | Compatible with publisher output | Compatible with WHEP | Compatible with HLS | Must obtain a MediaMTX-compatible token and use it for media requests | Not compatible with the current HS256 shared-secret token without additional identity infrastructure and config |

## Contract Constraints

Any future implementation must retain the existing contract: organization comes from the authenticated Sentira identity and server-side camera row; site comes from the camera row; camera ID and `playback` operation are explicit; issuer, audience, expiry, JTI, and request ID remain present; caller-supplied organization/site headers are ignored. Camera credentials must remain server-side.

## Decision

No option is selected or implemented in Phase 16. The local evidence justifies using MediaMTX for synthetic RTSP-to-HLS/WHEP media, but it does not justify claiming that the existing Sentira scoped token is consumed by MediaMTX. A safe next implementation requires choosing and validating one of the supported authorization boundaries above, then testing it through real media requests before adding a browser consumer.
