# Sentira AI - Phase 12 CCTV Onboarding & Connector Foundation Production Gate Report

## 1. PRODUCTION READINESS

**PRODUCTION READINESS = NOT READY.**

Phase 12 now contains a meaningful CCTV onboarding and Edge Connector foundation integrated with the existing NestJS, TypeORM, authentication, RBAC, camera, audit, entitlement, and stream-gateway architecture. The P0 setup-completion weakness was corrected: a setup cannot complete without a server-recorded `VERIFIED_CONNECTED` result and an organization-owned camera whose endpoint matches the verified endpoint.

However, the actual Sentira Edge Connector daemon, physical/local-network discovery, ONVIF execution, recorder channel enumeration, connector stream relay, and live hardware verification remain outstanding. The correct status is: automated foundation verified, production CCTV connectivity not yet demonstrated.

## 2. COMMIT AND WORKTREE

Current branch: `main`

Current HEAD: `51839aa` - `phase 12.7 update`

The worktree contains additional uncommitted Phase 12 changes for recorder/channel persistence, connector discovery-result reporting, API documentation, and architecture documentation. These changes were validated locally but are not represented by the current HEAD commit.

## 3. IMPLEMENTED

### Guided onboarding and state control

- `apps/web/src/app/cctv/page.tsx` provides the guided onboarding route for device type, viewing method, manufacturer, model, guide, connection, test, and support escalation.
- `apps/api/src/entities/cctv-setup-session.entity.ts` stores tenant-scoped resumable setup state, connector pairing metadata, progress, answers, and sanitized test results.
- `CctvService.updateSession()` accepts customer answers/current step but calculates stage and completion progress server-side.
- Client-submitted status, stage, completion percentage, and test result are not accepted through `UpdateSetupSessionDto`.
- `completeSession()` requires session status `VERIFIED`, test result `VERIFIED_CONNECTED`, an organization-owned camera, and matching endpoint fingerprint.

### Generic connector foundation

- `apps/api/src/modules/cctv/connectors/cctv-connector.ts` defines the connector capability contract.
- `generic-rtsp.connector.ts` provides bounded RTSP validation and deterministic failure results.
- `onvif.connector.ts` explicitly returns `DISCOVERY_UNAVAILABLE` when no Edge Connector is available; it does not fake cloud ONVIF discovery.
- `edge-connector.contract.ts` defines registration, heartbeat, discovery, device verification, and recorder-channel capabilities.

### Edge Connector pairing and reporting

- Setup sessions can generate short-lived, single-use pairing codes.
- Edge registration consumes the pairing code and receives a one-time registration token.
- Connector heartbeat authenticates the registration token and updates status/heartbeat metadata.
- Discovery requests are tenant/session/connector-bound.
- Connector discovery results are sanitized and persisted in the existing `discovered_cameras` table.
- The cloud returns explicit `DISCOVERY_UNAVAILABLE` until a real Edge Connector discovery agent is connected.

### Recorder/channel foundation

- `cctv_recorders` and `cctv_recorder_channels` entities and migration schema were added.
- Recorder channels have unique `(recorderId, channelNumber)` constraints.
- Recorder/channel records are organization-scoped and linked to connectors.
- Channel enumeration returns `CHANNEL_DISCOVERY_UNAVAILABLE` until an Edge Connector implements the contract.
- No fake recorder or channel verification is created.

### Security and compatibility

- Existing JWT and permission guards remain in use.
- Camera creation remains protected by the transactional organization camera entitlement service.
- Camera credentials remain encrypted with AES-256-GCM through the existing encryption service.
- Manual stream creation rejects common private, loopback, link-local, and `.local` destinations for cloud-side SSRF protection.
- Setup answers, test diagnostics, support context, and audit metadata sanitize credential-like values.
- Existing connector, discovered-camera, camera, site, organization, audit, and stream-gateway modules remain in place.

## 4. VERIFIED

The following commands were executed successfully for the current implementation:

- `npm --prefix apps/api test -- --runInBand`
- `npm --prefix apps/api run lint`
- `npm --prefix apps/api run build`
- `npm --prefix apps/web run lint`
- `npm --prefix apps/web run build`
- `git diff --check`

Observed results:

- API Jest: 19 suites passed, 63 tests passed, 1 suite skipped, 5 tests skipped.
- CCTV service tests: 10 tests passed, including:
  - setup tenant isolation
  - resumable setup session creation
  - rejection of unverified completion
  - rejection of cross-tenant camera completion
  - client workflow-state protection
  - support-context credential redaction
  - pairing-code creation and registration
  - authenticated heartbeat
  - truthful discovery-unavailable behavior
- Generic RTSP connector tests passed.
- ONVIF connector tests passed for deterministic unavailable behavior.
- API TypeScript typecheck passed.
- API production build passed.
- Web lint/typecheck passed with existing image optimization warnings.
- Web production build passed and generated `/cctv` and `/cctv/help` routes.
- Migration/schema code compiled successfully.
- No whitespace errors were reported.

## 5. PARTIALLY VERIFIED

- The database migration was compiled and statically inspected, but a real disposable PostgreSQL migration run was not executed in this validation pass.
- Tenant isolation is covered by service-level ownership queries and existing integration coverage, but new connector endpoints do not yet have a live HTTP two-tenant integration test.
- Pairing and heartbeat behavior are unit-tested with mocked repositories, not with a running Edge Connector client.
- Discovery-result persistence is implemented through the connector contract, but no actual local-network device reported results.
- Generic RTSP validation is implemented and unit-tested, but no physical RTSP camera was used.
- The existing Stream Gateway is healthy by source/build conventions, but a verified connector-to-MediaMTX stream handoff does not exist.
- FREE plan enforcement remains transactionally implemented for canonical camera creation/claim paths, but concurrent live bypass testing was not executed here.
- Web frontend behavior is build-verified but does not have browser automation or component tests.
- Support requests are persisted and sanitized, but support-agent assignment/status workflow is not operationally verified.

## 6. BLOCKED

- No physical CCTV hardware was available in this environment.
- No Sentira Edge Connector daemon/agent was available.
- No customer LAN was available for ONVIF or local discovery testing.
- No live production VPS verification was performed.
- No real recorder/NVR/DVR was available for channel enumeration.
- No browser automation test environment was used.

## 7. NOT IMPLEMENTED

- Actual Edge Connector daemon and outbound tunnel.
- Real ONVIF discovery, device information, media profile, and stream URI retrieval.
- Real local-network discovery execution.
- Real DVR/NVR recorder discovery and channel enumeration.
- Connector-to-stream-gateway/MediaMTX relay or path registration for connector cameras.
- Vendor-specific connectors for Hikvision, Dahua, Uniview, Axis, Hanwha, Bosch, CP Plus, TVT, Tiandy, and Reolink.
- Frontend channel selection and batch camera creation for DVR/NVR systems.
- QR scanning and vendor QR validation.
- Admin knowledge-base management UI.
- Troubleshooting decision-tree execution engine.
- CCTV funnel analytics and setup-success metrics.
- Support assignment console and agent workflow.
- Browser/component tests.
- Live connector contract integration tests.

No fake hardware verification or fabricated successful discovery result was added.

## 8. SECURITY

Implemented and source-verified:

- Setup completion requires server-owned `VERIFIED_CONNECTED` state.
- Client cannot force setup status, stage, completion percentage, or test result through the setup update DTO.
- Pairing codes are short-lived, hashed, and single-use.
- Connector registration tokens are generated once and only their hashes are persisted.
- Connector heartbeat/discovery operations require the registration token.
- Connector operations verify organization and setup-session association.
- Discovery result count is bounded.
- Support context and audit values redact password/token/secret/credential-like fields.
- Camera passwords are encrypted at rest and excluded from public camera responses by existing camera service behavior.
- Cloud-side manual stream creation rejects common private and loopback destinations.
- Existing JWT, permission, tenant-scoped repository, and audit patterns are preserved.

Open security work:

- DNS rebinding-safe connection execution requires a dedicated network worker/connector path.
- IPv6, multicast, broadcast, cloud metadata, redirect, and runtime egress protections require deeper network-level validation.
- Connector token revocation, rotation, rate limiting, and replay monitoring are not complete.
- Public camera response and stream URL exposure require a separate end-to-end API review before production release.

## 9. STREAM AND CAMERA VERIFICATION STATUS

The existing Stream Gateway consumes camera configurations through `/api/cameras/internal/all` and launches FFmpeg from `streamUrl` in `apps/stream-gateway/camera_manager.py`.

Connector-discovered cameras currently remain a foundation-only path. They do not yet provide a cloud-consumable `streamUrl`, tunnel, or MediaMTX path. Therefore:

- `DISCOVERED` does not mean configured.
- `CONFIGURED` does not mean verified.
- `VERIFIED_CONNECTED` is required before setup completion.
- Connector stream relay is not claimed.

The system must not report a connector camera as live until the Edge Connector and stream handoff are implemented.

## 10. FAILURE AND RECOVERY

Unit tests cover deterministic failure outcomes and rejected invalid state transitions. No controlled runtime restart/recovery matrix was executed for:

- connector offline/online transitions
- discovery timeout and cancellation
- connector token invalidation
- recorder enumeration timeout
- API/Redis/RabbitMQ/Stream Gateway restart during setup
- retrying setup after failed verification

This remains a release-gate item.

## 11. TEST STATUS

### Passed

- 19 API suites
- 63 API tests
- API lint/typecheck
- API production build
- Web lint/typecheck
- Web production build
- Generic RTSP connector unit tests
- ONVIF unavailable-path tests
- CCTV setup/pairing/security unit tests

### Skipped or unavailable

- Existing live integration suite is skipped unless `SENTIRA_LIVE_INTEGRATION=1` and a running API/database environment are available.
- No frontend browser tests exist.
- No physical hardware tests exist.
- No Edge Connector contract integration test exists.
- No live migration execution was included in this pass.

## 12. DOCUMENTATION

Updated or available documentation:

- `API.md` includes Phase 12 setup, pairing, heartbeat, discovery, channel, test, and completion endpoints.
- `CCTV_ARCHITECTURE.md` documents the Edge Connector boundary and verification invariant.
- `CCTV_KNOWLEDGE_BASE.md` documents backend-driven catalog and guide behavior.
- `CCTV_SUPPORT.md` documents support escalation and credential sanitization.

Remaining documentation work:

- `SECURITY.md` should include the finalized connector token and network-worker model.
- `DATABASE.md` should include recorder/channel and connection-test schema details.
- Stream documentation should describe the future connector-to-MediaMTX handoff.
- Deployment documentation should include migration execution and connector environment requirements.

## 13. FINAL GATE ANSWERS

1. Can `SETUP_INCOMPLETE` complete setup? **No; the backend requires `VERIFIED_CONNECTED`.**
2. Can the client force setup status/stage/completion? **Not through the setup update DTO; server derives workflow progress.**
3. Is generic RTSP validation implemented? **Yes, automated and bounded; physical camera not verified.**
4. Is ONVIF discovery implemented? **No; the connector abstraction returns deterministic unavailable status until an Edge Connector exists.**
5. Is local-network discovery implemented in the cloud? **No, intentionally.**
6. Is Edge Connector pairing foundation implemented? **Yes, unit-tested; no daemon integration verified.**
7. Are discovery results tenant/session-bound? **Yes in the service contract and persistence path.**
8. Are DVR/NVR entities present? **Yes, recorder/channel persistence is implemented; enumeration is unavailable without the Edge Connector.**
9. Are connector cameras in the stream pipeline? **No.**
10. Are camera credentials protected? **Encrypted at rest and sanitized in tested support/audit paths; full public-response review remains open.**
11. Is tenant isolation implemented? **Yes for the implemented service paths; new live HTTP integration coverage is pending.**
12. Is the FREE 3-camera limit enforced? **Yes through the existing transactional entitlement service.**
13. Are frontend browser tests present? **No.**
14. Are physical CCTV tests complete? **No.**
15. Is VPS production deployment verified? **No.**
16. Is Phase 12 production-ready? **No.**

## 14. REMAINING RISKS

- Edge Connector daemon and secure outbound transport are not implemented.
- Connector-discovered cameras cannot yet be relayed into MediaMTX/FFmpeg.
- DVR/NVR channel enumeration is contract-only.
- No real ONVIF or physical RTSP camera was tested.
- New connector endpoints lack live two-tenant HTTP integration coverage.
- Frontend has no automated interaction tests.
- Migration execution against PostgreSQL remains unverified.
- Existing web image warnings and deprecated `next lint` remain.
- Additional security review is required for runtime DNS/egress behavior.

## 15. OPERATIONAL CONCLUSION

Phase 12.7 provides a credible, truthful foundation for Edge Connector pairing, authenticated connector lifecycle, sanitized discovery reporting, and recorder/channel persistence. The critical completion invariant is enforced and automated validation is green. The implementation must remain classified **NOT READY** until a real Edge Connector, real stream handoff, physical or deterministic connector integration tests, migration execution, and production deployment verification are completed.

The repository does not claim physical CCTV verification, cloud-side private-network scanning, real ONVIF discovery, or production VPS readiness.
