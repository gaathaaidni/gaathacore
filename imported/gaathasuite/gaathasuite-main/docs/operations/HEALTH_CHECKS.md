# Health Checks

**Status:** IMPLEMENTED.

- `/health` and `/_health`: process-level response `{"status":"ok"}`.
- `/ready`: performs `SELECT 1` and returns `200` with database available, or `503` with database unavailable.
- Compose web healthcheck calls `/ready` on port 5000.

Health success does not prove migrations, Redis, workers, authentication, or every business workflow are healthy.
