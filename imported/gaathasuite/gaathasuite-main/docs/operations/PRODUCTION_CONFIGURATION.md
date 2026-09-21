# Production Configuration

**Status:** IMPLEMENTED configuration exists / NOT YET VERIFIED in a live environment.

`docker-compose.prod.yml` defines web, PostgreSQL 15, Redis 7, private database/Redis networking, persistent PostgreSQL/uploads volumes, required secrets, and a `/ready` healthcheck. Nginx proxies HTTPS to `127.0.0.1:5000`.

Required production values include `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SECRET_KEY`, `CORS_ORIGINS`, and `BASE_URL`. Keep PostgreSQL and Redis unexposed to the public network. Use [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) and [DEPLOYMENT_VPS.md](DEPLOYMENT_VPS.md).
