# Legacy Production Dependency Map

This document classifies legacy components that remain in the repository and whether they are still referenced by the production FastAPI path, migration tooling, deployment, tests, or only obsolete scripts.

## Summary

The active runtime is the FastAPI path under `backend/app` and `backend/entrypoint.sh`. The legacy Flask codebase remains in the tree for historical compatibility, but it is not the authoritative production startup path. The project has one authoritative startup flow:

`backend/entrypoint.sh` -> Alembic -> Uvicorn/FastAPI

The legacy Flask code is not currently required for the primary runtime, but it is not fully isolated from repo dependencies or documentation yet.

## Dependency matrix

| Component | Imported by production FastAPI code? | Imported by migrations? | Imported by deployment? | Imported by tests? | Imported only by obsolete scripts? | Completely unused? | Classification |
|---|---|---|---|---|---|---|---|
| `backend/entrypoint.sh` | Yes | No | Yes | No | No | No | Active runtime entrypoint |
| `backend/app/main.py` | Yes | No | Yes | No | No | No | Authoritative API startup |
| `backend/migrations/env.py` | No direct import; used by Alembic CLI | Yes | Yes via startup path | No | No | No | Required migration runtime |
| `backend/app/config.py` | Yes | No | Yes | Yes | No | No | Active config contract |
| `backend/config.py` | No | No | Possibly in legacy docs/scripts | No | Yes, legacy env defaults | No | Legacy-only config fallback |
| `backend/extensions.py` | No | No | No | No | Possibly older scripts | Yes, for legacy Flask runtime | Legacy Flask compatibility |
| `backend/init_db.py` | No | No | Possibly historical deployment | No | Yes | No | Legacy DB bootstrap helper |
| `backend/app/utils/schema_sync.py` | No | No | No | No | Some migration tooling likely references it | No | Historical compatibility helper |
| `backend/models.py` | No | No | No | No | Yes, legacy app scaffolding | No | Legacy Flask ORM surface |
| `backend/blueprints/**` | No | No | No | No | Yes, historical Flask views | No | Legacy Flask blueprint layer |
| `backend/requirements.txt` | Indirectly via environment install | Indirectly | Yes | Yes | No | No | Mixed stack dependencies remain |
| `scripts/*.py` | No | No | No | No | Yes | Mostly yes | Obsolete helper scripts |
| `ops/*` | No | No | Possibly via deployment automation | No | Yes | Not directly | Historical ops/runtime metadata |
| `docker-compose.yml` | N/A | N/A | Yes | No | No | No | Production deploy file |
| `docker-compose.prod.yml` | N/A | N/A | Yes | No | No | No | Production deploy file |
| `render.yaml`, `render.prod.yaml` | N/A | N/A | Yes | No | No | No | Deployment platform config |
| `scripts/init_local.sh` | No | No | No | No | Yes | No | Legacy local bootstrap |
| `scripts/postdeploy_migrate.sh` | No | No | Yes, legacy deployment path | No | Yes | No | Legacy migration hook |

## Determination by class

### A. Required by current FastAPI production

- `backend/entrypoint.sh`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/migrations/env.py`
- `backend/app/db.py`
- `backend/app/models/__init__.py`

These form the active runtime contract and are the only path that should be treated as authoritative.

### B. Migration / compatibility-only

- `backend/init_db.py`
- `backend/app/utils/schema_sync.py`
- historical migration revisions under `backend/migrations/versions/`
- preserved legacy singular compatibility tables and their foreign-key dependents

These remain for historical compatibility and should not be used in new application code.

### C. Legacy removable after dependency review

- `backend/config.py`
- `backend/extensions.py`
- Flask blueprints under `backend/blueprints/`
- Flask-only templates, form classes, and legacy route files
- old Flask dependencies in `backend/requirements.txt`

These are not used in the authoritative runtime path and should be removed or isolated from runtime if they are not needed for migration compatibility.

### D. Obsolete script-only assets

- `scripts/*.py` helper scripts that bootstrap or migrate old SQLite/Flask-only local environments
- older deployment hook scripts under `ops/` and `scripts/`

These should be treated as historical operational tooling and should not be imported by the production app.

## Decision

The legacy Flask stack is not required by the active FastAPI production path, but it is still present in requirements and repo code. The safe next step is to continue the isolation work already started: remove Flask imports from the production path, keep migration compatibility only as explicit exceptions, and prune legacy dependencies after final security verification. No direct removal has been performed here because the explicit requirement was to classify and isolate, not to delete blindly.

## Final status

Legacy Flask isolation status: FAIL for production-readiness. The runtime is FastAPI-only, but the legacy path has not been fully retired from the repo and runtime dependencies remain mixed.
