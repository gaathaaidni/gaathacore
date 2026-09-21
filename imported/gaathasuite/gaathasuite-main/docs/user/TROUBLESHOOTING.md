# Troubleshooting

**Status:** IMPLEMENTED as support guidance.

- Login failure: confirm the account is active and the API is reachable; never send tokens.
- Empty dashboard: confirm organization association and role.
- Missing module: confirm the route is mounted in the active FastAPI runtime; legacy source presence is not enough.
- Download failure: record the record type, timestamp, role, and visible error; do not expose signed URLs publicly.
- Slow or unavailable application: check `/health`, then `/ready`, logs, database health, and Redis status through the operator procedure.

Escalate with the [user-report diagnostic form](../developer/USER_REPORT_DIAGNOSTICS.md).
