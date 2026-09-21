# GaathaCore Staging Backup and Retention Policy

**Status:** Design plus local Core rehearsal evidence. No production backups or remote retention are claimed.

## Database Separation

Back up and restore each database independently. A backup of one database must never be treated as a backup of another.

| Database | Owner | Backup scope |
|---|---|---|
| `gaathacore_core` | GaathaCore | Core tables and `core_schema_migrations` |
| `gaathasuite` | Gaatha Suite | Suite database and separately managed uploads/media |
| `gaathapos` | Gaatha POS | POS database and separately managed application/media files |
| `sentira` | Sentira | Sentira database; object storage and stream media are separate scopes |
| `postpilot` | PostPilot | SQLite database plus local media/configuration files |

## Policy Template

The staging owner must replace these placeholders in an approved change record:

- Frequency: `[TBD per database owner]`
- Retention: `[TBD: daily/weekly/monthly windows]`
- Recovery point objective: `[TBD]`
- Recovery time objective: `[TBD]`
- Encrypted destination: `[TBD]`
- Restore approver: `[TBD]`

The repository does not claim that a remote backup store, schedule, encryption service, or retention job exists.

## Naming Convention

Use a database-specific, UTC-stamped name:

`<product>-<database>-<environment>-<format>-<YYYYMMDD>T<HHMMSS>Z.<extension>`

Examples use no real hostnames or credentials:

- `core-gaathacore_core-staging-custom-20260921T120000Z.dump`
- `suite-gaathasuite-staging-custom-20260921T120000Z.dump`

Never put passwords, tokens, connection URLs, or customer data in filenames.

## Required Controls

1. Use the owning database's credentials and tooling; never reuse `CORE_DATABASE_URL` for a product database.
2. Use custom-format PostgreSQL dumps where PostgreSQL is the owner, with ownership/ACL handling reviewed for the target environment.
3. Encrypt backups in transit and at rest; keep encryption keys separate from backup files.
4. Restrict backup read/write access to approved operators and automation identities.
5. Check the dump format and non-empty size immediately after creation. For PostgreSQL, inspect the archive table of contents with `pg_restore --list`.
6. Restore to a disposable database or isolated file volume before relying on the artifact.
7. Verify migration state, schema objects, representative relationships, and application readiness after restore.
8. Record backup time, source database identity, artifact checksum, integrity result, restore result, and failures without recording credentials.

## Failure Handling

A failed dump, checksum/integrity check, transfer, or restore is a failed backup run. Do not delete the previous known-good artifact, retry destructively against a live database, or mark the run successful. Preserve sanitized diagnostics and escalate to the database owner `[TBD]`.

## Current Evidence

- Core local custom-format backup and disposable restore were verified during Phase 10 using `scripts/core_staging.sh`.
- The wrapper now performs a local archive integrity listing before reporting a successful backup.
- Product backup automation, remote storage, scheduled retention, and product restore rehearsals are **DESIGNED ONLY / NOT VERIFIED**.
- No production backup was created.
