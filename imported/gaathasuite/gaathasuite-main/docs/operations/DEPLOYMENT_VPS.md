# VPS Deployment

**Status:** IMPLEMENTED deployment definitions / NOT YET VERIFIED live.

Use the repository's `docker-compose.prod.yml`, `Dockerfile`, `deploy/nginx/gaathasuite.conf`, and existing root deployment guides as the source of truth. Configure DNS for the public host, install Docker and Compose, provide required secrets, keep PostgreSQL/Redis private, start the stack, configure Nginx/TLS, and verify `/health`, `/ready`, login, logs, and uploads.

Do not expose database or Redis ports publicly. Apply migrations through the documented Alembic process and maintain a tested backup before schema changes.
