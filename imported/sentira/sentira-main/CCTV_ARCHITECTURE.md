# CCTV Guided Onboarding Architecture

Sentira's guided CCTV flow lives in `apps/api/src/modules/cctv` and uses the existing NestJS, TypeORM, JWT, permission, audit, camera, site, and entitlement services.

## Flow

1. The web client creates an organization-scoped setup session.
2. The customer identifies device type, viewing method, manufacturer, and model. Each answer is persisted so the session can resume.
3. Manufacturer/model compatibility and setup guides are read from the CCTV catalog. Unknown compatibility remains unknown.
4. The connection stage either uses a real connector discovery result or asks for a user-provided video address through the existing manual camera service.
5. A structured test result is stored. The system never reports success without an existing camera status or connector result.
6. Failed setup can create a support request with sanitized context.

Automatic local discovery remains connector-dependent. The cloud must not scan arbitrary customer networks or request private addresses directly.

## Data model

## Phase 13 edge runtime

`apps/edge-connector` is an outbound-only Python daemon. It performs bounded WS-Discovery ONVIF endpoint
detection and real RTSP `OPTIONS` checks on the customer LAN, reports sanitized results over the existing
authenticated API, and persists its registration identity with local file permissions `0600`. It does
not open an inbound port, accept arbitrary cloud destinations, or treat discovery as verification.

The current runtime does not yet implement ONVIF SOAP media-profile calls, recorder adapters, cloud command
polling, or connector-to-MediaMTX stream relay. Those remain explicit unavailable capabilities. A discovered
device is not a configured camera, and a configured camera is not active until a trusted connection test
returns `VERIFIED_CONNECTED`.
- `cctv_manufacturers`: catalog ownership and generic manufacturer metadata.
- `cctv_models`: device type, discovery methods, and verified/unknown protocol compatibility.
- `cctv_setup_guides`: versioned, backend-driven steps and troubleshooting.
- `cctv_setup_sessions`: resumable customer state and sanitized test result.
- `cctv_support_requests`: tenant-scoped escalation state and diagnostic context.

Add a manufacturer/model through admin APIs, then add only compatibility information that has a source and verification state.

## Phase 12 connector boundary

`EdgeConnectorContract` defines registration, heartbeat, discovery, device verification, and recorder-channel enumeration. The cloud implementation now supports short-lived setup-session pairing, one-time registration tokens, authenticated heartbeat, tenant/session-bound discovery-result reporting, and recorder/channel persistence.

No daemon is included in this repository. Until an edge agent implements the contract, discovery and channel enumeration return explicit unavailable results. A discovered device is not a configured camera, and a configured camera is not active until a trusted connection test returns `VERIFIED_CONNECTED`.
