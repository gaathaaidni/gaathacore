# GAATHA SUITE — Deployment Runbook

## Objective

Prepare and validate a controlled release candidate for a VPS deployment without modifying production data.

## Required preflight checks

1. Confirm source revision and branch.
2. Verify the database and Redis services are healthy.
3. Ensure environment secrets are present in the target deployment environment.
4. Confirm all migration commands are run against the intended database.
5. Confirm the target database is not the production database during preflight testing.

## Deployment sequence

1. Pull the release candidate.
2. Verify Docker Compose configuration.
3. Validate environment variables.
4. Run database migration on the target database.
5. Start the services.
6. Verify `/ready` and `/health` endpoints.
7. Verify login and tenant-scoped access.
8. Verify a representative ERP workflow.
9. Verify logs and service health.
10. Confirm rollback is available.

## Command outline

```bash
git status --short
git rev-parse HEAD
cd backend
python -m alembic -c migrations/alembic.ini upgrade head
python -m alembic -c migrations/alembic.ini check
cd ..
npm run build
docker compose config
```

## Rollback guidance

- Roll back only to the last known-good image or revision.
- Do not destructive-drop the production database during a rollback unless the disaster-recovery plan explicitly allows it.
- Keep the previous database snapshot and backup artifact available.

## Final safety rule

No automatic production deployment is performed from this repository in this session. The deployment is considered release-candidate ready only when the preflight checks and smoke tests pass in the target environment.
