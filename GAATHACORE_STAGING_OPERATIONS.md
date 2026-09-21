# GaathaCore Staging Operations

## Scope

This document covers local/staging operation of five logically separate PostgreSQL databases. It does not authorize VPS access, production changes, product migrations, database merging, billing, or adapter implementation for Sentira/PostPilot.

## Topology and ownership

| Database | Owner | Core responsibility |
|---|---|---|
| `gaathacore_core` | GaathaCore | Users, organizations, memberships, projects, project memberships, module access, RBAC, audit events, usage events, and the independent Core migration history |
| `gaathasuite` | Gaatha Suite | Suite business tables, Suite users/authentication, sessions/JWT, Suite configuration, and Suite migrations |
| `gaathapos` | Gaatha POS | POS restaurants, users/authentication, sessions, products, operational data, and POS migrations |
| `sentira` | Sentira | Sentira organizations/sites/cameras/events/workers and Sentira migrations |
| `postpilot` | PostPilot | PostPilot application data, local media/provider configuration, and PostPilot persistence |

Core must not copy product business tables, join across databases, or own product credentials. Suite and POS mappings store explicit source-service/source-ID references only. Sentira and PostPilot adapters are not implemented.

## Core-owned tables

`users`, `organizations`, `organization_memberships`, `projects`, `project_memberships`, `module_access`, `audit_events`, `usage_events`, `suite_user_map`, `suite_organization_map`, `suite_project_map`, `pos_user_map`, `pos_restaurant_map`, and `core_schema_migrations`.

## Environment configuration

Core uses environment injection; no credentials belong in source, reports, Compose files, or logs.

- `CORE_ENV`: `development`, `test`, `staging`, or `production`.
- `CORE_DATABASE_URL`: complete PostgreSQL URL. Required for staging and production; never a SQLite URL.
- `GAATHACORE_DB_PATH`: optional development/test-only SQLite path. It must not be used in staging or production.
- `CORE_POSTGRES_DB`, `CORE_POSTGRES_USER`, `CORE_POSTGRES_PASSWORD`, `CORE_POSTGRES_PORT`: local Compose inputs only. Use secret-managed values outside local development.

Product configuration remains product-owned. Evidenced names include:

- Suite: `APP_ENV`, `DATABASE_URL`, `SECRET_KEY`, plus its product-owned Redis/mail/OAuth settings.
- POS: `APP_ENV`, `DATABASE_URL`, `SECRET_KEY`, plus its product-owned Redis/session settings.
- Sentira: `NODE_ENV`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET`, and its product-owned service URLs/tokens.
- PostPilot: `FLASK_ENV`, `FLASK_DEBUG`, and its product-owned provider/page/upload settings. PostPilot is not approved for shared public exposure.

These names describe existing product boundaries; values must be supplied by each service's deployment environment. Do not reuse a product `DATABASE_URL` for Core.

## Networking

The local Core Compose service binds PostgreSQL to loopback only. In staging, databases should be reachable only by their owning service networks or private network controls. Do not expose PostgreSQL to the public internet. The five databases may share a PostgreSQL cluster when deployed, but remain separate database names and migration histories.

## Migration and rollback

Core migrations live under `core/migrations/` and use `core_schema_migrations`. Run Core migration status and upgrade independently from Suite, POS, Sentira, and PostPilot migrations. Never combine migration histories or run a cross-database transaction.

Recommended staging sequence:

1. Verify environment configuration and database reachability.
2. Back up the target database before schema changes.
3. Run Core migration status, then Core upgrade to its current head.
4. Verify Core readiness and no pending Core migrations.
5. Run each product's own migration process separately, only under that product's owner and change plan.
6. Validate product and Core health independently.

Rollback means restoring the affected database backup or applying a tested Core downgrade in isolation. Product rollback is product-owned. Do not roll back one database by modifying another database.

## Controlled staging migration and rollback runbook

Run this procedure against a private, disposable or approved staging target only. Do not combine product steps, migration histories, or transactions.

1. Validate configuration: confirm the owning service's environment, required secret injection, environment name, and database URL format. Never print the values.
2. Verify database identity: run the owning service's identity check and confirm database name, user, and server version are expected. Core uses `scripts/core_staging.sh identity`.
3. Verify private connectivity: confirm the target is reachable only through the approved private/local path. Core uses the loopback-only Compose service.
4. Create and integrity-check a backup of the affected database. Core uses `scripts/core_staging.sh backup`; restore is disposable-only.
5. Check migration status without creating history where possible. Core uses `scripts/core_staging.sh migrate-status`.
6. Apply only the affected service's reviewed migration. Core uses `scripts/core_staging.sh migrate-up`; product owners use their own migration commands.
7. Verify migration head and no pending migrations.
8. Verify readiness and service health. Core uses `scripts/core_staging.sh health`; product readiness remains product-owned.
9. Run focused tests for the affected service and adapter boundary.
10. Record target identity, migration result, readiness result, test command/result, backup artifact/checksum, operator placeholder, and timestamp without secrets.
11. Use rollback only when explicitly authorized. Prefer a tested migration downgrade where supported; otherwise restore the affected database to a disposable target first and verify it before any approved recovery action.

### Independent migration histories

| Service | Database | Migration owner and boundary |
|---|---|---|
| Core | `gaathacore_core` | `core/migrations/runner.py`, `core_schema_migrations` |
| Gaatha Suite | `gaathasuite` | Suite-owned Alembic/Flask migration process |
| Gaatha POS | `gaathapos` | POS-owned Alembic/Flask migration process |
| Sentira | `sentira` | Sentira-owned TypeORM migration process |
| PostPilot | `postpilot` | PostPilot-owned persistence/migration process |

No cross-database transaction, automatic destructive command, or shared migration history is permitted.

## Resource and connection considerations

Core currently opens short-lived psycopg2 connections for operations and does not define a shared application pool. No arbitrary production pool size, connection limit, CPU limit, or memory limit is applied here. Before staging approval, the owner should document the PostgreSQL `max_connections` budget, service connection concurrency, connect timeout, statement timeout, transaction timeout, and expected restart behavior.

The current concrete controls are:

- Core database connections use a three-second timeout for identity/health CLI checks.
- Migration and service writes use transaction context managers; failed transactions are rolled back by the connection context and do not silently continue.
- Core Compose restarts the local PostgreSQL service unless stopped by the operator and exposes only a loopback port.
- Database isolation is maintained by separate database names and migration histories.

Pool sizing, server resource limits, queue capacity, and product database settings remain designed-only until measured staging capacity and product-owner requirements exist.

## Local staging automation

The non-production wrapper `scripts/core_staging.sh` operates only on `docker-compose.core.yml` and the Core database. It has no VPS or production mode.

```text
scripts/core_staging.sh up
CORE_DATABASE_URL=<injected-local-url> scripts/core_staging.sh identity
CORE_DATABASE_URL=<injected-local-url> scripts/core_staging.sh migrate-status
CORE_DATABASE_URL=<injected-local-url> scripts/core_staging.sh migrate-up
CORE_DATABASE_URL=<injected-local-url> scripts/core_staging.sh health
scripts/core_staging.sh backup
scripts/core_staging.sh logs
scripts/core_staging.sh down
```

`backup` writes a custom-format dump to `CORE_BACKUP_FILE` or its local `/tmp` default. `restore` is intentionally destructive and refuses to run unless both `CORE_STAGING_DISPOSABLE=1` and `CORE_RESTORE_CONFIRM=RESTORE_CORE_DISPOSABLE` are set. It must be used only with a disposable Core database and an existing backup. The wrapper never resets, downgrades, restores, or removes volumes implicitly.

Secret injection details, ownership, backup retention, and monitoring contracts are documented in `GAATHACORE_STAGING_OWNERSHIP.md`, `GAATHACORE_BACKUP_RETENTION.md`, `GAATHACORE_MONITORING_CONTRACT.md`, and the safe-value `.env.example` template. These documents do not provision a secret manager, remote backup store, monitoring provider, or production connection.

## Health and readiness

`core.operations.core_health()` reports non-sensitive process, configuration, PostgreSQL connectivity, migration, and schema state. `ready` means configuration is valid, PostgreSQL is reachable, migration history exists, and no Core migrations are pending. Process availability alone is not readiness. Health output must not contain URLs, passwords, stack traces, or product data.

Core has no HTTP application service in this repository. Readiness is safely available through `core_health()` and `python -m core.operations_cli health`; the CLI returns non-zero when not ready and emits no credentials or URLs. A new gateway or HTTP endpoint would invent an unowned service boundary, so HTTP integration is **DESIGNED ONLY**, not implemented. Product `/health` and `/ready` endpoints remain product-owned and are not substituted by Core.

## Backup responsibilities

Back up `gaathacore_core` independently with PostgreSQL tooling such as `pg_dump`; restore it independently with `pg_restore` or `psql` into a disposable database first. Verify Core users, organizations, projects, memberships, mappings, audit, usage, and migration state after restore. Product databases require their own backup owners and rehearsals. Never use production credentials for local rehearsal.

## What is not implemented

Sentira and PostPilot Core adapters, shared gateway deployment, production secret provisioning, VPS operations, cross-database joins, product data migration, pricing, billing ledgers, subscriptions, invoices, payments, charging, and public PostPilot exposure are not implemented.
