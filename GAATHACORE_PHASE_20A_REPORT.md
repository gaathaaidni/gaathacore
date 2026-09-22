# GaathaCore Phase 20A — Disposable Local Media Runtime Report

**Run date:** 2026-09-22 (UTC)  
**Mode:** implementation-first, local-only  
**Result:** BLOCKED — this workspace cannot start the repository-defined
container runtime, and no host replacements are installed. No deployment,
production configuration, credentials, VPS resources, DNS, Nginx, or databases
were accessed or changed.

## Runtime configuration inspected

The existing Sentira configuration already contains the intended local media
architecture; no new architecture was introduced.

* `imported/sentira/sentira-main/docker-compose.yml` declares MediaMTX as
  `bluenviron/mediamtx:latest` and mounts the repository MediaMTX configuration.
  It also builds the Stream Gateway from its existing Dockerfile.
* `imported/sentira/sentira-main/apps/stream-gateway/Dockerfile` already installs
  `ffmpeg` in the Stream Gateway image. Adding it again would be redundant and
  would change no runtime capability without a container engine.
* `imported/sentira/sentira-main/docker-compose.phase20a.yml` is an existing,
  local-only disposable validation topology. It uses the declared MediaMTX image,
  two isolated source MediaMTX instances, deterministic FFmpeg `lavfi` sources,
  a local stub API, and the real Stream Gateway/`CameraStreamManager`. Its
  configuration supplies only phase-specific local tokens and no camera
  credentials.
* `mediamtx.phase20a-main.yml` retains HTTP authorization through the actual
  Stream Gateway callback at `http://127.0.0.1:8001/media/auth`. It has not been
  replaced or relaxed.
* The stub API contains only two deterministic, credential-free RTSP source
  URLs: `camera-a` in `org-a/site-a` and `camera-b` in `org-b/site-b`. It also
  exposes a local disable-A control for the intended reconciliation smoke test.

## Disposable local validation procedure

When a Docker-compatible container engine is available, the existing procedure
is the repository-defined phase-20A Compose topology:

```bash
cd /workspace/gaathacore/imported/sentira/sentira-main
docker compose -f docker-compose.phase20a.yml up --build --abort-on-container-exit
```

This procedure must be run only on a disposable local machine. It starts
`mediamtx`, `source-a`, `source-b`, `local-api`, `source-publisher-a`,
`source-publisher-b`, and `stream-gateway`. It neither requires a physical
camera nor uses a production credential. Stop and remove it with:

```bash
docker compose -f docker-compose.phase20a.yml down --volumes --remove-orphans
```

## VERIFIED

* The focused Stream Gateway suite contains **19 tests** by source inspection.
* The existing `CameraStreamManager` creates three FFmpeg child processes per
  managed camera: AI JPEG extraction, rolling-buffer segmentation, and RTSP
  publication. Its existing tests cover cleanup of all three children.
* Existing Phase 20 test source covers two tenant-scoped publication paths,
  cross-tenant authorization rejection, expiration, disabled-camera
  revalidation, and reconciliation.
* The existing phase-20A Compose files use deterministic synthetic sources and
  route both camera streams through the real `CameraStreamManager`, rather than
  using the standalone fixture as the primary manager proof.

## PARTIALLY VERIFIED

* The repository configuration is prepared for the required two-stream live
  run. The stream paths configured by the manager are
  `sentira/org-a/site-a/camera-a` and `sentira/org-b/site-b/camera-b`.
* The Stream Gateway Dockerfile declares FFmpeg, and the repository declares a
  MediaMTX image. Binary availability inside those images could not be observed
  because no supported container engine is installed in this workspace.

## NOT VERIFIED

No live claims are made for the following items because no service could be
started:

* FFmpeg version and MediaMTX version.
* MediaMTX configuration validation by the MediaMTX binary.
* Stream Gateway startup.
* Simultaneous manager publication of A and B to MediaMTX.
* Parent/child HLS playlists, init segments, or media segments.
* Live callback status codes for A-to-A, B-to-B, A-to-B, B-to-A, no-token, or
  expired-token requests.
* Disable-A reconciliation against a live publication while B continues.
* Live inspection of AI JPEG, rolling buffer, and publication process cleanup.
* Browser `/media-test` and WHEP playback. No browser probe was run.

## BLOCKED

The exact local blockers observed were:

| Requirement | Observed result |
| --- | --- |
| Docker daemon/client | `docker: command not found` |
| Docker Compose | unavailable (`docker` and `docker-compose` absent) |
| Alternative container runtime | `podman` and `nerdctl` unavailable |
| Host FFmpeg | unavailable |
| Host MediaMTX | unavailable |
| Sentira Node dependencies | root and API `node_modules` unavailable |
| Stream Gateway Python dependencies | no virtual environment; `fastapi`, `aiohttp`, and `jwt` unavailable in host Python |

The prescribed existing runtime depends on container images for both FFmpeg and
MediaMTX. Installing ad-hoc host binaries or replacing the Compose topology
would not use the repository-defined runtime and would not satisfy this phase.
Accordingly, the live run was stopped rather than introducing a workaround.

## TEST RESULTS

| Check | Result |
| --- | --- |
| `docker version --format '{{.Server.Version}}'` | BLOCKED: `docker` command absent |
| `docker compose -f docker-compose.phase20a.yml config` | BLOCKED: Docker Compose unavailable |
| `ffmpeg --version` | BLOCKED: binary absent |
| `mediamtx --version` | BLOCKED: binary absent |
| `python -m pytest --collect-only -q apps/stream-gateway/tests` | BLOCKED: 3 collection errors from missing host dependencies/import path; no tests collected |
| `/tmp/gaathacore-phase20a-venv/bin/pip install -r apps/stream-gateway/requirements.txt pytest` | BLOCKED: the configured package proxy returned HTTP 403, so an isolated test environment could not be installed |
| Stream Gateway focused tests | BLOCKED in this workspace; source count is 19 but the tests could not execute |
| `python -m py_compile apps/stream-gateway/*.py scripts/phase20a_stub_api.py` | PASS |
| `npm --workspace apps/api run test -- --runInBand` | BLOCKED: `jest` is absent because API dependencies are unavailable |
| `npm --workspace apps/web run lint` | BLOCKED: `next`, React, and TypeScript type dependencies are absent; fallback TypeScript diagnostics therefore fail on missing modules |
| Phase 19 media checks | BLOCKED: require the same unavailable FFmpeg, MediaMTX, and container engine |
| Browser/WHEP | NOT VERIFIED: no browser runtime was used, per phase instruction |

## Final runtime state

No Phase 20A containers, streams, local volumes, or child processes were
created. Phase 20 can be rerun completely only after this workspace provides a
Docker-compatible container engine capable of running the existing
`docker-compose.phase20a.yml` topology (and access to its declared images). At
that point, execute the procedure above and record observed binary versions,
HTTP status codes, lifecycle behavior, and process cleanup; this report must
not be treated as live validation evidence.
