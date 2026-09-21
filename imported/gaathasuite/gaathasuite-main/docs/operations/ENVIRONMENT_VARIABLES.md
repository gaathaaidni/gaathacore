# Environment Variables

**Status:** IMPLEMENTED reference. See [Configuration](../developer/CONFIGURATION.md) for the broader application list.

Production Compose requires `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SECRET_KEY`, `CORS_ORIGINS`, and `BASE_URL`; it sets internal `DATABASE_URL` and `REDIS_URL`. Application templates additionally define authentication, email, OAuth, AI, payment, and company values.

Secret values must be injected by the deployment system, never committed or printed in logs. Legal identity variables are not currently established in runtime configuration and must remain business placeholders until confirmed.
