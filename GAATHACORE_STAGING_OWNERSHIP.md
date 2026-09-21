# GaathaCore Staging Ownership Model

**Status:** Design for local/staging planning only. Ownership marked `[TBD]` is not assigned by this document.

## Principles

- Each product owns its application data, credentials, migrations, queues, and operational runtime.
- Core owns only platform records and the Core migration history in `gaathacore_core`.
- No person, company, credential, infrastructure host, or production responsibility is inferred here.
- A staging owner must be named and access-approved before a shared staging deployment is created.

## Ownership Matrix

| Surface | Owning service or boundary | Staging responsibility | Current status |
|---|---|---|---|
| Core platform | GaathaCore | Core configuration, platform health, Core PostgreSQL schema, Core adapters | Local implementation exists; staging owner `[TBD]` |
| Gaatha Suite | Gaatha Suite | Suite runtime, Suite data, Suite auth, Suite migrations and readiness | Product-owned; owner `[TBD]` |
| Gaatha POS | Gaatha POS | POS runtime, restaurant data, POS auth, POS migrations and readiness | Product-owned; owner `[TBD]` |
| Sentira | Sentira | Sentira runtime, camera/event data, workers, gateway, and product migrations | Adapter not implemented; owner `[TBD]` |
| PostPilot | PostPilot | PostPilot runtime, local media/provider configuration, and product persistence | Adapter not implemented; public exposure remains blocked |
| PostgreSQL databases | Each database owner | Separate database identity, access, schema, capacity, backup, and restore | Five logical databases; shared cluster, if any, requires approval |
| Redis/queues | Product owner using the service | Namespace, credentials, queue lifecycle, retry/DLQ behavior, and recovery | Product-specific; no shared broker assumed |
| Object storage/media | Product owner using storage | Bucket/key ownership, access policy, retention, integrity, and restore | Sentira/object storage is product-owned; Core has no media store |
| Backups | Database/product owner | Schedule, encryption, restricted access, integrity check, disposable restore, and evidence | Policy designed in `GAATHACORE_BACKUP_RETENTION.md`; execution `[TBD]` |
| Secrets | The service that consumes each secret | Injection, least privilege, rotation, revocation, and non-disclosure | Local templates only; secret manager `[TBD]` |
| Monitoring | Staging operations owner `[TBD]` | Probe execution, alert routing, acknowledgement, escalation, and evidence | Contract designed; no external monitoring connected |
| Migrations | Owner of the affected database | Preflight, backup, migration status, apply, verify, and record | Core runbook implemented; product procedures remain separate |
| Rollback | Owner of the affected database/service | Authorization, restore or tested downgrade, verification, and incident record | Core disposable restore is locally guarded; staging approval `[TBD]` |

## Decision Rights

The following decisions require an explicitly recorded staging owner and approval before execution: shared PostgreSQL cluster use, network exposure, secret-manager selection, backup destination/retention, migration window, destructive restore, and rollback authorization. This document does not grant that authority.

## Database Boundaries

| Database | Data owner | Migration history |
|---|---|---|
| `gaathacore_core` | GaathaCore | `core_schema_migrations` and `core/migrations/` |
| `gaathasuite` | Gaatha Suite | Suite-owned Alembic/Flask migration history |
| `gaathapos` | Gaatha POS | POS-owned Alembic/Flask migration history |
| `sentira` | Sentira | Sentira-owned TypeORM migration history |
| `postpilot` | PostPilot | PostPilot-owned SQLite/product migration behavior |

No cross-database transaction, join, shared migration history, or credential reuse is part of this model.

## Handoff Record

Before a future staging deployment, fill in the approved owner, contact path, environment name, database identities, backup location, monitoring destination, maintenance window, and rollback approver in the staging change record. Do not add those values to this repository unless they are non-sensitive and intentionally public.
