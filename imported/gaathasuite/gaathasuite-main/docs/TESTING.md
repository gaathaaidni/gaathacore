# Testing

## Available checks

```sh
python -m compileall -q backend
npm --prefix frontend run build
python -m pytest backend/tests
```

The backend test foundation is in `backend/tests/test_auth_tenant_foundation.py`. It covers registration/login, tenant-scoped dashboard results, and rejection of organization-admin superadmin escalation.

Set `TEST_DATABASE_URL` to a dedicated PostgreSQL database before running the API tests. Tests reset their database tables and never use a production URL. Without `TEST_DATABASE_URL`, pytest skips these tests explicitly; that is an environment blocker, not a pass.

## CI

CI installs `backend/requirements.txt`, runs Alembic from `backend/`, executes pytest against a PostgreSQL service, lints the backend/frontend, and builds the frontend. Clean migration validation remains blocked until the multiple-root/multiple-head migration graph is reconciled.

## Required future checks

Add route-level cross-tenant IDOR tests, permission-matrix tests, migration upgrade/downgrade tests, webhook idempotency tests, upload security tests, and end-to-end business workflow tests.
