# GAATHA SUITE — Release Candidate Checklist

## PROVEN LOCALLY

- [x] FastAPI web container starts after migrations
- [x] `db` healthy and `redis` running
- [x] `/health` returns HTTP 200
- [x] `/ready` returns HTTP 200 with database available
- [x] Web restart recovers to healthy state
- [x] Core CRM, sales, fulfillment, purchasing, receipt, inventory, invoice, and vendor-bill flows pass PostgreSQL-backed tests
- [x] Backend suite passes: 29 passed
- [x] Frontend build passes
- [x] Alembic check reports no new operations
- [x] Docker Compose configuration validates
- [x] Phase 1 security, accounting, immutability, and backup/restore evidence preserved

## PROVEN ON VPS

- [ ] No VPS deployment was performed in this session.
- [ ] No live DNS/TLS change was executed against `gaathasuite.gaatha.tech`.

## NOT YET VERIFIED

- [ ] Run the deployment runbook on the intended VPS
- [ ] Verify production database identity and backup artifact before migration
- [ ] Verify PostgreSQL and Redis remain private to the deployment network
- [ ] Verify HTTPS reverse proxy, forwarded headers, API routing, and explicit CORS
- [ ] Verify login and tenant-scoped representative workflow through the public HTTPS endpoint
- [ ] Verify logs contain no startup, migration, or unhandled application errors
- [ ] Verify rollback to the previous image/revision

## Decision

Current status: **YELLOW — controlled VPS rehearsal required**

Do not declare GREEN until every unchecked VPS item has executable evidence.
