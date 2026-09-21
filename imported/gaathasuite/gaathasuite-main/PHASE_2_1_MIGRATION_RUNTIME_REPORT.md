# GaathaSuite Phase 2.1 Migration + Runtime Report

Audit date: 2026-09-10

## Executive Status

**Phase 2.1 status: SUPERSEDED by Phase 2.2.**

The critical schema/runtime mismatch described in this report was reconciled during Phase 2.2. The current Phase 2.2 report records the updated evidence and remaining blockers.

## Migration Graph Before

**Roots:** `2aa562de3542`, `v2_schema_001`, `202604101345`

**Heads:** `20260104_ic`, `202604101345`, `20260613_add_hr_tenant_columns`, `v2_schema_001`, `4af2d8a7e1b3`

**Branches and dependencies:**

- `2aa562de3542` was the original root. It branched to `358f784f255a` and `0002_add_is_superadmin`.
- `358f784f255a` branched to `76d2578a7a97 -> 7e5ffd3e0afd` and `4af2d8a7e1b3`.
- `0002_add_is_superadmin -> 0003_add_invitation_table -> 20251217_add_coupons_orgpayments`.
- `20251217_add_coupons_orgpayments` and `7e5ffd3e0afd` merged at `5fc668732c41`.
- `5fc668732c41` branched to `20260613_add_hr_tenant_columns` and `20260103_ec -> 20260104_os -> 20260104_oc -> 20260104_ic`.
- `v2_schema_001` was an independent compatibility root.
- `202604101345` was an independent attendance root.

`alembic upgrade head` failed before changes with Alembic's multiple-head error. `alembic upgrade heads` succeeded on an empty PostgreSQL database, proving the DDL bodies were individually compatible but did not establish a single logical head.

## Migration Graph After

A no-op merge revision was added:

- Canonical root set preserved: `2aa562de3542`, `v2_schema_001`, and `202604101345` remain historical roots because their bodies represent separate legacy/compatibility transitions.
- Canonical head: `phase21_merge_20260910`.
- Merge revision: `20260910_phase21_merge_heads.py` merges `20260104_ic`, `202604101345`, `20260613_add_hr_tenant_columns`, `v2_schema_001`, and `4af2d8a7e1b3`.
- No migration history was deleted or marked current automatically.

Executed result:

```text
phase21_merge_20260910 (head)
```

## PostgreSQL Clean Migration

**PASS for migration execution.** A fresh PostgreSQL 15 Docker container was created with an empty database. `alembic upgrade head` completed successfully. A second `alembic upgrade head` was a no-op and `alembic current` remained at the merge head.

**RESOLVED in Phase 2.2.** A reconciliation migration creates the FastAPI plural tables and preserves legacy singular tables as compatibility-only tables. Real authentication now works against the Alembic-created schema.

## Alembic Current/Heads

- `alembic current`: `phase21_merge_20260910 (head) (mergepoint)`
- `alembic heads`: exactly one head, `phase21_merge_20260910`

## Database Schema Verification

**PASS for the reconciled FastAPI contract.** PostgreSQL inspection verified the application-facing tables, keys, constraints, indexes, and nullability. Legacy singular tables remain preserved and excluded from active FastAPI schema drift comparison.

The clean schema does not yet prove the FastAPI tenant contract because the table names and model contracts diverge. Tenant columns/foreign keys exist on several legacy tables, but the application-facing plural tables are absent. Full tenant-owned-table verification, cascade review, and schema reconciliation remain blockers.

## Backend Dependency Verification

**PASS for installation/import.** A local `.venv-phase21` was created and `backend/requirements.txt` was installed. The real application import completed with `APP_IMPORT_OK` after fixing import-path defects in the FastAPI surface.

## Automated Tests

**PASS for the repository's discovered backend tests.** `backend/tests` contains two tests. Against a separate empty PostgreSQL test database:

```text
2 passed, 21 warnings
```

The tests cover registration/login plus a tenant-scoped dashboard count and organization-admin superadmin escalation prevention. They do not cover the full Phase 2.1 authentication or tenant matrix requested in the brief.

## Authentication Tests

**PASS for executed coverage.** Registration/login, invalid login, inactive-user rejection, malformed-token rejection, unauthorized access, tenant dashboard scoping, and privilege escalation now run against an Alembic-provisioned database. Expired-token, logout/revocation, password reset, and the full role matrix remain NOT VERIFIED.

## Tenant Isolation Tests

**PARTIAL / NOT VERIFIED.** Organization-scoped dashboard counting passes against the reconciled schema. Full cross-tenant CRUD and malicious IDOR coverage is not present.

## API Smoke Tests

- `GET /health`: **PASS**, HTTP 200, `{"status":"ok"}`.
- `GET /ready`: **PASS**, HTTP 200, database available.
- Invalid login against clean migrated PostgreSQL: **PASS**, HTTP 401.
- Registration, valid login, and authenticated dashboard against clean migrated PostgreSQL: **PASS**.

## Docker Runtime Test

- Production Docker image build: **PASS**. Multi-stage backend and frontend image built successfully.
- PostgreSQL container: **PASS**, healthy.
- Redis container: **PASS**, running.
- Web container: **BLOCKED BY ENVIRONMENT**. Direct connections from web to both `db:5432` and `redis:6379` timed out while the Docker bridge gateway was reachable. The healthcheck was changed to Python standard-library URL probing.
- API health through Compose: **FAIL / NOT VERIFIED** because the web container never reached Uvicorn.

## Security Verification

- Unsafe/default secret fallbacks: **ABSENT in the active FastAPI helpers**. Legacy root configuration paths still contain fallback behavior and require retirement/isolation.
- Development Compose database defaults: **PRESENT** in `docker-compose.yml` as development fallbacks; production Compose requires supplied variables.
- Hardcoded production credentials: **PRESENT** in legacy/default configuration paths; actual values are not reproduced here.
- Password reset placeholder hashing: **ABSENT** in the edited FastAPI task; it now uses the User hashing method.
- Password/JWT/API-key logging: **NOT VERIFIED** across the full legacy surface.
- Unsafe wildcard CORS: **NOT VERIFIED** by full deployment review.

## Observability

**PARTIAL.** Uvicorn startup and readiness failures are logged. The global exception handler logs unexpected exceptions. Full authentication-failure and authorization-failure event coverage, plus sensitive-log review across legacy modules, is NOT VERIFIED.

## Production Boot Path

**PARTIAL.** `backend/entrypoint.sh` has one FastAPI/Alembic path and does not perform automatic migration-state repair or `create_all`. However, Flask-Migrate and legacy Flask boot scripts remain in the repository and requirements:

- Required by current FastAPI production boot: `backend/entrypoint.sh`, `backend/app/main.py`, `backend/migrations/env.py`.
- Required only by legacy migration/history or compatibility tooling: `ops/run_migrations_staging.sh`, `scripts/render_postdeploy.sh`, `scripts/postdeploy_migrate.sh`, legacy migration helpers.
- Legacy/likely removable after dependency review: `backend/extensions.py`, Flask-only blueprint/runtime modules and Flask dependencies.
- Unknown/needs investigation: scripts that import `create_app` and legacy deployment documentation.

The production runtime path is not safe to call unambiguous until legacy paths are retired or explicitly isolated and the schema mismatch is resolved.

## Remaining Blockers

1. Resolve Docker bridge inter-container connectivity in the execution environment.
2. Add and execute full tenant CRUD/IDOR coverage.
3. Retire or isolate remaining legacy fallback configuration and Flask paths.
4. Complete expired-token, logout/revocation, password-reset, and full role-matrix testing.

## Exact Commands Used

```text
python -m venv .venv-phase21
.venv-phase21/bin/pip install -r backend/requirements.txt
cd backend && DATABASE_URL=... ../.venv-phase21/bin/alembic -c migrations/alembic.ini heads
cd backend && DATABASE_URL=... ../.venv-phase21/bin/alembic -c migrations/alembic.ini upgrade head
cd backend && DATABASE_URL=... ../.venv-phase21/bin/alembic -c migrations/alembic.ini current
cd backend && DATABASE_URL=... ../.venv-phase21/bin/alembic -c migrations/alembic.ini upgrade head
PYTHONPATH=. DATABASE_URL=... TEST_DATABASE_URL=... ../.venv-phase21/bin/python -m pytest tests -q
PYTHONPATH=. DATABASE_URL=... SECRET_KEY=... ../.venv-phase21/bin/uvicorn app.main:app --host 127.0.0.1 --port 5050
curl -i http://127.0.0.1:5050/health
curl -i http://127.0.0.1:5050/ready
docker compose --project-directory /workspaces/gaathasuite -f /workspaces/gaathasuite/docker-compose.yml build
docker compose --project-directory /workspaces/gaathasuite -f /workspaces/gaathasuite/docker-compose.yml up -d
docker compose ... ps
docker compose ... logs --no-color --tail=100 web
```

## Final Phase Status

**SUPERSEDED.** Phase 2.2 resolves clean-schema compatibility and live authentication. Phase 2.2 remains NOT COMPLETE because Docker runtime networking, full IDOR coverage, and legacy-path cleanup remain unresolved.
