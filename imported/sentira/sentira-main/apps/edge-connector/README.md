# Sentira Edge Connector

This is the Phase 13.2 outbound-only connector runtime. It runs inside a customer CCTV network and never opens an inbound listener.

## Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export SENTIRA_API_URL=https://sentira.example/api
export SENTIRA_SETUP_SESSION_ID=<setup-session-id>
export SENTIRA_PAIRING_CODE=<short-lived-pairing-code>
export SENTIRA_POLL_INTERVAL_SECONDS=10
export SENTIRA_POLL_MAX_WAIT_SECONDS=20
export SENTIRA_COMMAND_TIMEOUT_SECONDS=120
export SENTIRA_ONVIF_TIMEOUT_SECONDS=15
export SENTIRA_ONVIF_RETRY_COUNT=1
export SENTIRA_ONVIF_RETRY_DELAY_SECONDS=0.25
python main.py
```

The pairing code is used only for first registration. The connector stores its connector ID and registration token in `~/.config/sentira-edge/identity` with mode `0600`; the raw token is not logged. Set `SENTIRA_CONNECTOR_TOKEN_FILE` to use another restricted path.

The daemon now performs authenticated heartbeats, polls the cloud command queue, acknowledges commands, runs bounded RTSP and ONVIF actions, and reports results back to the API. The command plane is always server-owned and the edge never sets a camera to `VERIFIED_CONNECTED` without a valid command result and cloud-side validation.

## Supported actions

This implementation intentionally exposes only the capabilities that are deterministic and bounded:

- `PING`
- `GET_CAPABILITIES`
- `DISCOVER_ONVIF`
- `TEST_RTSP`
- `GET_ONVIF_DEVICE_INFORMATION`
- `GET_ONVIF_MEDIA_PROFILES`
- `GET_ONVIF_STREAM_URI`
- `VERIFY_ONVIF_DEVICE`

The ONVIF commands use real SOAP/HTTP requests from the connector. Their payload accepts `xaddr` or `deviceServiceUrl`, `username`, `password`, and optional `profileToken`; credentials are used locally and removed from returned results. `GET_ONVIF_STREAM_URI` deterministically selects the first returned profile when no token is supplied. `VERIFY_ONVIF_DEVICE` checks device information, service discovery, profiles, stream URI, and bounded RTSP OPTIONS connectivity, and reports `verified: false` when any check fails.

The implementation is tested with deterministic XML fixtures and is not equivalent to physical-camera validation. No real hardware was available for this repository run.

## ONVIF errors

Failures are structured and safe for cloud reporting. Common codes are `ONVIF_AUTH_FAILED`, `ONVIF_DEVICE_UNREACHABLE`, `ONVIF_TIMEOUT`, `ONVIF_SOAP_FAULT`, `ONVIF_INVALID_RESPONSE`, `ONVIF_SERVICE_UNAVAILABLE`, `ONVIF_PROFILE_NOT_FOUND`, and `ONVIF_STREAM_URI_UNAVAILABLE`.

## Live hardware validation

Before claiming production CCTV onboarding, test from the connector host on the same LAN as a real ONVIF camera or NVR:

1. Enable ONVIF on the device and create a dedicated least-privilege account.
2. Record the device service URL and RTSP network path without placing credentials in shell history or logs.
3. Pair the connector, then issue each command through the cloud command API: device information, media profiles, stream URI, and RTSP test.
4. Run full verification and confirm every required check is true, including real RTSP connectivity.
5. Record connector version, model, sanitized error code, latency, and whether real media packets reached the downstream pipeline.

Hardware results must be reported separately from fixture/mock results. Never include passwords, raw tokens, or credentialed URLs in evidence.

## Security

- outbound HTTPS only to the configured Sentira API
- no inbound listener
- no arbitrary redirects or DNS rebinding to untrusted destinations
- credential redaction in all returned command results
- bounded command batch size and command timeout
- no local credential logging

## Service hardening

Run under a dedicated unprivileged account, restrict the identity file to that account, allow outbound HTTPS only to the Sentira API, and do not expose connector ports through the firewall. The runtime has no self-update mechanism and does not accept arbitrary cloud destinations.
