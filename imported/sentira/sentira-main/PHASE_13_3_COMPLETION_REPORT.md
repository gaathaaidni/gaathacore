# Sentira Phase 13.3 Completion Report

## Executive Status

**PARTIALLY IMPLEMENTED; MOCK/FIXTURE VERIFIED; NOT LIVE-HARDWARE VERIFIED.**

Phase 13.3 now contains a real ONVIF SOAP/HTTP integration path in the edge connector. Device information, media profiles, stream URI retrieval, and verification orchestration are implemented with bounded transport, structured errors, WS-Security UsernameToken support, service discovery, and credential redaction.

The implementation was tested with deterministic SOAP fixtures. No physical ONVIF camera, NVR, or customer CCTV deployment was available, so live hardware verification and production-ready CCTV onboarding are not claimed.

## Implemented

- `apps/edge-connector/onvif/` client package separating transport, SOAP construction/parsing, authentication, models, and errors.
- `GetDeviceInformation` parsing for manufacturer, model, firmware, serial number, and hardware ID.
- `GetServices` discovery for device, Media, and Media2 service namespaces.
- `GetProfiles` parsing for profile token/name, source and encoder tokens, resolution, encoding, and FPS where supplied.
- `GetStreamUri` with requested profile validation and deterministic first-profile selection when no token is provided.
- `VERIFY_ONVIF_DEVICE` orchestration covering device information, service discovery, profiles, stream URI, and bounded RTSP OPTIONS testing.
- WS-Security UsernameToken password digest generation with nonce and UTC timestamp; optional HTTP Basic authentication is also supported by the transport.
- Namespace-prefix-independent XML parsing and SOAP fault detection.
- Bounded request timeout, retry count, retry delay, polling-safe execution, and sanitized structured failures.
- Existing `PING`, `GET_CAPABILITIES`, `DISCOVER_ONVIF`, and `TEST_RTSP` behavior preserved.
- Existing cloud command queue, connector authorization, tenant scoping, acknowledgement, lifecycle, and stale-result protections preserved.

## Tested

### Edge tests

```bash
python3 -m pytest -q apps/edge-connector/
```

Result after ONVIF implementation and hardening:

- `9 passed`

Coverage includes:
- SOAP fixture parsing.
- Namespace-independent response traversal.
- Well-formed namespace-qualified SOAP requests.
- WS-Security digest generation without plaintext password output.
- SOAP Fault mapping.
- Device information command integration.
- Stream URI credential redaction.
- Invalid endpoint rejection.
- Existing RTSP and discovery regressions.

### API validation

```bash
npm --prefix apps/api run lint
npm --prefix apps/api run build
npm --prefix apps/api test -- --runInBand src/modules/cctv/cctv.service.spec.ts
git --no-pager diff --check
```

Results:
- API lint passed.
- API build passed.
- CCTV command lifecycle regression passed: `12 passed, 12 total`.
- Diff check passed.

## Mock / Fixture Evidence

The ONVIF tests use deterministic XML responses for:
- `GetServices`.
- `GetDeviceInformation`.
- `GetProfiles`.
- `GetStreamUri`.
- SOAP Fault.

These tests prove request construction, parsing, error mapping, orchestration, and redaction. They do not prove interoperability with any particular vendor or physical device.

## Live Hardware

**NOT TESTED.**

No real ONVIF-capable camera or NVR was connected during this implementation. There is no claim of:
- physical device authentication success;
- vendor interoperability;
- real stream URI usability;
- real RTSP media availability;
- end-to-end camera onboarding;
- downstream real-packet delivery.

The live procedure is documented in `apps/edge-connector/README.md` and must be executed from an installed connector on the same LAN as the target camera/NVR.

## Security

- Camera credentials are accepted only as command input and used locally by the edge connector.
- WS-Security password digests, nonces, authorization headers, and passwords are not returned in results or logs by the ONVIF implementation.
- Stream URIs are redacted if a device embeds credentials.
- The command executor performs a second recursive credential-field sanitization before cloud reporting.
- HTTP redirects are disabled for SOAP transport.
- Endpoint scheme, host, and port are validated; multicast, unspecified, and reserved literal IP destinations are rejected.
- SOAP calls and retries are bounded by configured timeout, retry count, and retry delay.
- No shell commands, arbitrary filesystem paths, or public-cloud camera connections are introduced.
- Phase 13.2 connector authorization and tenant isolation remain unchanged.

## Limitations

- No vendor-specific ONVIF quirks or digest-authentication challenge flow were validated against hardware.
- HTTP Basic and WS-Security UsernameToken are supported; devices requiring vendor-specific authentication extensions may remain unavailable.
- Verification reports `verified: false` with `PARTIALLY_VERIFIED` when RTSP or another required check fails; it never claims success from reachability alone.
- NVR channel enumeration and vendor-specific recorder adapters remain outside this phase.
- The current repository has fixture tests, not a live mock HTTP server integration test.

## Next Gate

Before Sentira can claim production-ready CCTV onboarding:

1. Run the documented procedure against at least one real ONVIF camera and one real NVR where supported.
2. Verify device information, profile enumeration, stream URI retrieval, RTSP connectivity, and full verification from the edge connector.
3. Record exact model, firmware, ONVIF endpoint, sanitized result codes, latency, and downstream real-packet evidence without credentials.
4. Exercise authentication failures, timeouts, malformed responses, and service endpoint variants on hardware.
5. Confirm cloud-side onboarding persists only a camera that passes the server-controlled verification policy.

**Final decision: Phase 13.3 is implemented and fixture-verified, but remains NOT READY for a live hardware or production-readiness claim.**
