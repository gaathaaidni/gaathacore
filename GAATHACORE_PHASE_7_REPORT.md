# GAATHACORE Phase 7 Report

**Phase:** 7 - PostgreSQL Core Architecture
**Date:** 2026-09-21
**Status:** IMPLEMENTED locally; PostgreSQL execution BLOCKED until a local `CORE_DATABASE_URL` is supplied. No production action was taken.

## 1. Objective

Move Core from the Phase 4 SQLite proof toward a dedicated PostgreSQL platform database while preserving independent product databases and native product authentication.

## 2. Architecture decision

Core uses a dedicated PostgreSQL database selected by `CORE_DATABASE_URL`. A small SQL migration runner was chosen because this workspace has no existing root Core framework; it is versioned, deterministic, Core-only, and uses its own `core_schema_migrations` table. The existing Suite Alembic decision was inspected but not reused across database boundaries.

## 3. Why SQLite was temporary

Phase 4 SQLite was useful for local authorization and adapter proofs, but it is not suitable as the canonical beta/VPS multi-tenant store. It remains explicitly test/development scaffolding through `GaathaCoreService`; the factory rejects it in production and selects PostgreSQL whenever `CORE_DATABASE_URL` is present.

## 4. PostgreSQL and five-database strategy

The target topology is five separate databases: `gaathacore_core`, `gaathasuite`, `gaathapos`, `sentira`, and `postpilot`. Core owns platform entities only. Product records, credentials, sessions, and product migrations remain product-owned. No cross-database joins were added.

## 5. Core schema and migrations

Migration `001_initial.sql` implements users, organizations, organization memberships, projects, project memberships, project-scoped module access, append-oriented audit events, immutable-oriented usage events, and explicit Suite/POS mapping tables. Audit and usage indexes cover tenant, project, actor/user, module, timestamp, correlation, and usage idempotency. `001_initial.down.sql` provides isolated rollback. Future pricing, billing, subscription, wallet, invoice, and payment tables are NOT IMPLEMENTED.

## 6. Identifier and boundary strategy

Core IDs are UUID strings and never assume product-local numeric IDs. Product references are explicit mapping tables with string-normalized local IDs. The mapping boundary is `Suite user/org/project -> Core identity/org/project` and `POS user/restaurant -> Core identity/project`, with Core authorization required after native product authentication. Sentira and PostPilot adapters remain DESIGNED, not implemented.

## 7. Suite and POS adapter impact

Both adapters preserve their injected service API and now use the Core service factory when no service is supplied. Suite keeps its auth, password hashes, sessions/JWT, and organization logic. POS keeps Flask auth, sessions, restaurant records, and restaurant authorization. No production users or product tables were migrated.

## 8. RBAC and modules

The canonical roles and explicit permission registry remain centralized in Core. Module keys are `suite`, `pos`, `sentira`, and `postpilot`; access is project-scoped and does not inherit between projects unless explicitly configured. Cross-organization, cross-project, inactive-membership, and disabled-module checks remain enforced.

## 9. Audit, usage, and billing readiness

Audit and usage persistence now have PostgreSQL representations. Usage supports organization, project, module, operation/feature, user, source service, quantity, unit, timestamp, idempotency key, correlation ID, and metadata. No charging, pricing, payment provider, subscription, or live billing was implemented. Future billing must consume immutable usage events.

## 10. Local development and Docker

`docker-compose.core.yml` defines an isolated localhost-only PostgreSQL service using database `gaathacore_core`, with development-only defaults. It does not alter product Compose files or expose PostgreSQL publicly. Run it only against local data, then set `CORE_DATABASE_URL` and run the Core migration runner through `PostgresCoreService`.

## 11. Testing and migration results

IMPLEMENTED tests: `tests/test_core_phase7_postgres.py` covers migration head, tenant isolation, module access, audit persistence, and usage idempotency when PostgreSQL is available.

VERIFIED: `pytest -q tests/test_core_phase4.py tests/test_suite_adapter_phase5.py tests/test_pos_adapter_phase6.py tests/test_core_phase7_postgres.py` produced **22 passed, 3 skipped**. The three skips are PostgreSQL tests because `CORE_DATABASE_URL` was not configured. `python -m compileall -q core tests` and `git diff --check` passed.

BLOCKED: empty database -> migration -> current head, status with no pending migrations, and downgrade/upgrade could not be executed without a local PostgreSQL server. They must be run against an isolated local database before production planning.

## 12. Security validation

No credentials or production URLs were added. Production factory selection requires PostgreSQL. The local Compose binding is loopback-only. Product schemas and migration histories were not edited. Core does not trust product IDs as Core IDs, and authorization checks remain server-side. Secret scanning and production migration validation remain pending local PostgreSQL execution.

## 13. Files changed

Added: `core/config.py`, `core/factory.py`, `core/postgres.py`, `core/migrations/`, `requirements-core.txt`, `docker-compose.core.yml`, and `tests/test_core_phase7_postgres.py`.

Updated: `core/platform.py`, `core/suite_adapter.py`, and `core/pos_adapter.py`.

Existing unrelated worktree changes were preserved. No commit or push was made.

## 14. Failures, limitations, and rollback

New failures: no test failures; PostgreSQL checks are BLOCKED by missing local PostgreSQL configuration. Existing deprecation warnings from imported Suite dependencies remain. Rollback is to stop using the factory and retain the explicit SQLite test backend, or downgrade Core migration `001` in an isolated database. Product databases are unaffected.

## 15. Production/VPS implications and non-deployment

No VPS, production database, credentials, DNS, Nginx, reverse proxy, migration, user migration, product migration, payment integration, or billing action was performed. Production requires a separately provisioned `gaathacore_core`, secret-managed `CORE_DATABASE_URL`, backups, TLS/network controls, migration rehearsal, and tenant data migration planning.

## 16. Phase 8 handoff

Recommended objective: provision a disposable local/staging PostgreSQL environment, execute and test migration upgrade/downgrade, implement a complete repository abstraction or SQLAlchemy-backed Core service if justified by runtime needs, then add Sentira/PostPilot adapters only after their identity and tenant boundaries are documented. Do not begin production deployment or billing.

## Phase 8 addendum

Phase 8 validated the isolated `gaathacore_core` PostgreSQL database with real Docker PostgreSQL. Migration `001` upgraded deterministically, downgraded, and re-upgraded successfully; the final catalog contained only Core tables and migration history. The focused Phase 4/5/6/7 suite passed **24 tests**, including Suite and POS with PostgreSQL Core enabled. A POS route test was aligned to seed through the PostgreSQL Core factory when `CORE_DATABASE_URL` is set. Repository-wide `pytest -q` remains blocked by the unrelated imported Suite `auto_signup_test.py` collection script, which raises `SystemExit(1)` for missing product columns. No production or VPS action occurred. See `GAATHACORE_PHASE_8_REPORT.md`.