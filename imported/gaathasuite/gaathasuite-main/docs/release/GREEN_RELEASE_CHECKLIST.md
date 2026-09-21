# Green Release Checklist

## Current evidence status

This checklist reflects the actual verified state of the repository in the current environment.

### Verified

- Backend bootstrap smoke tests pass in the current environment.
- Frontend production build succeeds.
- Docker Compose configuration resolves successfully.
- Compile checks pass.
- `git diff --check` passes.

### Not yet verified

- Alembic migration head against a dedicated PostgreSQL test database
- full tenant isolation route matrix and negative tests
- full RBAC object-level authorization matrix
- accounting journal/invoice/payment integrity tests
- sales/procurement/inventory/expense workflow verification
- backup/restore rehearsal
- Redis/Celery operational startup tests

## Release gate

1. Ensure `DATABASE_URL` and `SECRET_KEY` are defined in the target environment.
2. Run `pytest` against the app test suite.
3. Run `npm --prefix frontend run build`.
4. Run `python -m compileall -q backend`.
5. Run `git diff --check`.
6. Run `docker compose config`.
7. Validate `GET /health`, `GET /_health`, and `GET /ready` in a live environment.
8. Verify migration head using an isolated Postgres database.
9. Execute tenant isolation negative tests.
10. Execute accounting and workflow integration tests.
11. Rehearse backup and restore against a disposable environment.
12. Review legacy runtime boundary and worker validity before release.

## Final recommendation

Current status: YELLOW

The project is not ready to claim a green release without completing the remaining verification work above.
