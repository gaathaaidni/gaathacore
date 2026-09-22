# GaathaCore Phase 20 - Sentira Multi-Tenant Media Isolation & Lifecycle Validation

**Date:** 2026-09-22  
**Scope:** Sentira only  
**Status:** **YELLOW**

## Implemented

- Added periodic camera projection reconciliation to the existing `CameraStreamManager`.
- Disabled or removed cameras now stop through the existing manager task and process cleanup path.
- Organization/site reassignment stops the old publication before the next enabled reconciliation starts the new path.
- Added `CAMERA_REFRESH_SECONDS` with a five-second local default.
- Preserved the existing three-child manager process group: AI JPEG, RollingBuffer, and RTSP publication.
- Extended the existing `/media-test` page to issue bearer-authorized HLS parent requests for Organization A and B and display the HTTP result.
- Added focused regression coverage for tenant paths, callback authorization, lifecycle reconciliation, process cleanup, and credential non-exposure.

No Core mapping, production/VPS/DNS/Nginx/database change, dependency installation, commit, or push was performed.

## VERIFIED

- Existing Stream Gateway tests plus new Phase 20 coverage: **19 passed, 0 failed**.
- Python compilation and `compileall`: passed.
- Editor diagnostics for all six edited files: no errors.
- `git diff --check`: passed.
- Local Compose interpolation with disposable placeholder values: passed.
- Direct `/media/auth` callback contract tests prove:
  - Organization A token to A path: allowed.
  - Organization B token to B path: allowed.
  - A token to B path: rejected.
  - B token to A path: rejected.
  - Missing token: rejected.
  - Expired token: rejected.
  - Camera/site/org claim mismatch: rejected.
  - Stale A authorization after camera reassignment: rejected.
  - Disabled camera state: rejected.
- Publication paths are independently generated as `sentira/org-a/site-a/camera-a` and `sentira/org-b/site-b/camera-b`.
- Publication command tests confirm the source camera password is not present in manager arguments.
- Existing manager cleanup test confirms all three registered child processes are terminated.
- Existing AI JPEG and RollingBuffer tests remain passing.
- The MediaMTX callback remains configured at `http://stream-gateway:8001/media/auth` in the checked-in local configuration.

## PARTIALLY VERIFIED

- Lifecycle behavior is verified through manager reconciliation tests, but not against a running API, MediaMTX instance, or live HLS session.
- The `/media-test` page can make authorized and rejected HLS requests using bearer headers. Browser rendering and actual playback were not run in this container.
- Reassignment is hardened locally by stopping the old manager task before the new tenant path is used. Persistence/API reassignment support is not present as a user-facing camera mutation in the inspected Sentira controller.
- Publication-token handling remains a local FFmpeg query argument. It is not a camera credential, but it is visible to local process inspection.

## NOT VERIFIED

- Two independent manager-produced synthetic FFmpeg streams running simultaneously into MediaMTX.
- Actual MediaMTX HLS parent, child, init, and segment HTTP status results for both manager-produced streams in this Phase 20 run.
- Physical or remote camera operation.
- WHEP SDP negotiation.
- Instant revocation of already-established HLS sessions.
- Live delete/unassign lifecycle against API and MediaMTX.
- Browser-native video playback of the current HLS response.

## BLOCKED

- Live media validation was blocked because `ffmpeg` and `mediamtx` executables are unavailable in the container.
- API Jest and frontend build validation were blocked because the Sentira dependency tree is absent (`node_modules` missing; `jest` unavailable).
- No browser automation/runtime was available for a playback screenshot or native playback probe.

## SECURITY FINDINGS

- No camera password is transported by the manager projection, placed in FFmpeg arguments, sent to the AI Worker, returned by the media-test page, or included in tests/reports.
- The existing local publication token is passed as an RTSP query parameter and is therefore visible in the local FFmpeg command line. This is an operational hardening concern. A larger publication-auth redesign was intentionally not introduced.
- Fresh media authorization re-checks current camera organization, site, enabled state, and token claims. Existing HLS sessions are not claimed to be revoked instantly.

## REMAINING RISKS

- The required acceptance criterion for concrete simultaneous MediaMTX streams remains open until a runtime with FFmpeg and MediaMTX is available.
- The five-second reconciliation interval permits a short window before a disabled/deleted/reassigned camera publication is stopped; fresh playback authorization is still checked against current state.
- WHEP and browser playback remain separate validation gaps.
- The publication token command-line exposure should be addressed before production hardening.

## Recommendation

Keep the phase **YELLOW** and do not advance to Core mapping yet. The single most important blocker is a disposable local media runtime capable of running two actual CameraStreamManager FFmpeg process groups against MediaMTX and recording the real A/B HLS callback HTTP results.
