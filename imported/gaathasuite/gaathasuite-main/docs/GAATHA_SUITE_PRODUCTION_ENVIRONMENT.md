# GAATHA SUITE — Production Environment Configuration

## PROVEN LOCALLY

- `DATABASE_URL` and `SECRET_KEY` are required at startup and are enforced by the active FastAPI configuration.
- The local Compose profile is able to start the stack with PostgreSQL and Redis available to the app.
- The local application health and readiness checks pass under the local runtime profile.

## PROVEN ON VPS

- No VPS deployment was performed.
- No live production secret, database hostname, or TLS configuration was validated on the target VPS.

## NOT YET VERIFIED

- `gaathasuite.gaatha.tech` TLS and reverse-proxy behavior against the deployed application.
- production `CORS_ORIGINS` matching the real browser origin
- actual public network exposure of PostgreSQL/Redis on the target VPS
- final application startup and rollback behaviour in the target environment

## Required runtime secrets

These are required for a production install and must be managed outside the repository:

- `DATABASE_URL`
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD` if Redis auth is enabled
- `JWT_SECRET` if the deployment uses a dedicated JWT secret not bundled into the app settings

## Public or deployment-managed configuration

- `APP_ENV=production`
- `CORS_ORIGINS=https://gaathasuite.gaatha.tech`
- `BASE_URL=https://gaathasuite.gaatha.tech`
- `REDIS_URL=redis://redis:6379/0`
- `PORT=5000`
- `HOST=0.0.0.0`

## Example production-safe environment values

```env
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://gaatha:<strong-password>@db:5432/gaatha
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<strong-random-secret>
PORT=5000
HOST=0.0.0.0
CORS_ORIGINS=https://gaathasuite.gaatha.tech
BASE_URL=https://gaathasuite.gaatha.tech
```

## Security guidance

- Never commit real secrets.
- Do not expose PostgreSQL or Redis publicly.
- Do not use `*` for CORS when authenticated requests require browser credential handling.
- Use a dedicated production secret manager or deployment environment secret store.

## Deployment notes

The repository already contains a production-oriented Docker Compose configuration for the web, DB, and Redis stack. The deployed web service must be kept behind HTTPS and a reverse proxy or platform ingress that terminates TLS. This session did not execute that live deployment step.
