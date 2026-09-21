# Observability

## IMPLEMENTED — NOT VERIFIED
The API accepts `X-Correlation-Id` or generates a UUID and returns it in the response header. Production logs must include this ID plus tenant/resource identifiers and must never include credentials, tokens, or secrets. `/api/system/health` performs a PostgreSQL `SELECT 1`; services without a verified probe are returned as unavailable/degraded, not healthy.
