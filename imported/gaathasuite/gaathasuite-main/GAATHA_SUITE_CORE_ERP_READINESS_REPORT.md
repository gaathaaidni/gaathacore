# Gaatha Suite Beta RC Hardening Report

## Status: YELLOW

The release-candidate hardening changes are code-verified and suitable for controlled deployment review. VPS deployment, live health checks, and database-backed regression tests were not fully verified in this environment.

## Release Identity

- Repository: `gaathaaidni/gaathasuite`
- Branch: `main`
- Current commit: `270ab9f`
- Scope: health/readiness, SPA fallback security, headers, production Compose, and focused tests only.

## Code Verified

- `/health` and `/_health` remain lightweight `200` JSON liveness endpoints.
- `/ready` executes `SELECT 1`, returns stable JSON with `200` when available and `503` when unavailable.
- Docker healthchecks use Python `urllib` against `/ready`; no `curl` dependency is required.
- Sensitive dotfiles, infrastructure/configuration paths, backups, SQL files, source manifests, and Docker files are denied before SPA fallback.
- Unknown `/api/*` and `/auth/*` paths return JSON `404`; legitimate frontend routes return the built `index.html`.
- `/static` remains mounted separately and static assets are served normally.
- Existing security headers remain present. Added CSP allows the two scripts currently referenced by `frontend/index.html`; `Permissions-Policy` is restrictive.
- Production Compose binds web to loopback, exposes neither PostgreSQL nor Redis, requires production secrets, uses `APP_ENV=production`, and defaults to the existing `gaatha_postgres_data` volume.
- No schema or migration files were changed. Alembic remains the migration mechanism.

## Tests Executed

Focused release tests:

```text
cd /workspaces/gaathasuite/backend && . .venv/bin/activate && TEST_DATABASE_URL=postgresql+asyncpg://gaatha:gaatha@localhost:5432/gaatha python -m pytest tests/test_business_workflow_execution.py -k release -q
```

Result: `2 passed, 4 deselected, 10 warnings`.

The full suite was also attempted:

```text
TEST_DATABASE_URL=postgresql+asyncpg://gaatha:gaatha@localhost:5432/gaatha python -m pytest -q
```

Result: `9 passed, 10 errors`. The errors are database fixture setup failures because PostgreSQL at `localhost:5432` refused connections. No tenant-isolation assertion was changed; the existing tenant tests could not complete without PostgreSQL.

Additional checks:

- `python -m compileall -q app blueprints tests`: passed.
- `npm --prefix frontend run build`: passed, Vite generated the current production bundle.
- `git diff --check`: passed.
- `docker compose -f docker-compose.prod.yml config --quiet`: passed with explicit placeholder settings.

## Docker Verification

`docker build --build-arg BUILD_ID=270ab9f -t gaatha:rc-270ab9f -f /workspaces/gaathasuite/Dockerfile /workspaces/gaathasuite` completed successfully with the legacy builder after BuildKit encountered a transient cache/snapshot error. Image: `gaatha:rc-270ab9f`, digest `sha256:735de1d537926aa038818af3565c97280a101d760e9e167328602129cec6aeed`.

## Database Volume Identity

Production Compose now defaults to the existing live volume `gaatha_postgres_data`, matching the reported VPS volume. An explicit `POSTGRES_VOLUME_NAME` override remains available. No volume was removed, renamed, or touched.

## VPS Deployment Verified

Not verified. This task did not modify the VPS, inspect live secrets, run a deployment, or perform a live `/health` and `/ready` smoke test. The stale live image and old Compose deployment remain deployment risks until the RC image is deployed and checked.

## Remaining Blockers

- Restore or provide an isolated PostgreSQL service and rerun the full suite, including tenant-isolation tests.
- Inspect `/static/dist/build-id.txt` in the built image as an additional deployment check.
- Deploy the RC through the existing VPS process and verify `/health`, `/_health`, `/ready`, static assets, sensitive-path `404`s, and Nginx routing.
- Existing product-level beta limitations remain, including incomplete AP journal posting and broader browser/deployment verification.

## Controlled VPS Deployment Decision

**Repository ready for controlled VPS deployment review: YES.**

**Repository and VPS release fully verified: NO.** Status remains **YELLOW** until the database-backed suite, clean image build, and VPS smoke test pass.
