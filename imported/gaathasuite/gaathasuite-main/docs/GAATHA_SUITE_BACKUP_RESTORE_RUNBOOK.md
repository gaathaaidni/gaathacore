# GAATHA SUITE — Production Backup and Restore Runbook

## Purpose

This runbook defines the protected backup and recovery process for Gaatha Suite production deployments. It is designed to keep data recoverable, preserve uploaded content, and prevent accidental destructive actions against the live database.

This document is operational guidance and must be executed only by an authorized operator. It must never be used to modify production data in-place without explicit approval and a recovery window.

---

## 1. Scope

This runbook covers:

- scheduled PostgreSQL backups
- off-site replication of backup archives
- uploads and file volume backup
- retention policy and deletion rules
- disposable restore drill procedures
- failure alerting and verification checks

This runbook does not authorize production database restores or destructive cleanup. All restore work must target a disposable database or an approved recovery environment.

---

## 2. Production backup architecture

Gaatha Suite stores critical state in PostgreSQL and file uploads in a persistent volume. A complete recovery requires both parts.

Required data sources:

- PostgreSQL primary database: application data, tenant records, accounting, audit tables
- uploads volume: documents, attachments, generated reports, user-submitted files
- deployment configuration: environment file, TLS certificates, docker compose configuration

The repository includes backup helpers in [scripts/backup_database.py](../scripts/backup_database.py) and [scripts/restore_database_test.py](../scripts/restore_database_test.py), which provide a safe default pattern for dump creation and disposable restore rehearsal.

---

## 3. Scheduled PostgreSQL backups

### 3.1 Schedule

Run a PostgreSQL dump at a fixed interval appropriate to the business RPO. Recommended starting point:

- full logical backup every 24 hours
- encrypted copy pushed to an off-site backup location every run
- alert if the backup job is missing, fails, or is older than the configured threshold

### 3.2 Command

From the production host, run:

```bash
mkdir -p /var/backups/gaathasuite
cd /opt/gaathasuite
set -a; . ./.env; set +a
python3 scripts/backup_database.py \
  --database-url "$DATABASE_URL" \
  --backup-dir /var/backups/gaathasuite \
  --retention-days 30
```

Recommended cron or systemd schedule:

```cron
0 2 * * * /usr/bin/env bash -lc 'cd /opt/gaathasuite && python3 scripts/backup_database.py --database-url "$DATABASE_URL" --backup-dir /var/backups/gaathasuite --retention-days 30 >> /var/log/gaathasuite-backup.log 2>&1'
```

### 3.3 Backup type

Use PostgreSQL custom-format dumps for recoverability and integrity checks:

```bash
pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file /var/backups/gaathasuite/gaatha-$(date -u +%Y%m%dT%H%M%SZ).dump
```

Do not store raw SQL text as the only backup; custom-format dumps are easier to validate and restore safely.

---

## 4. Off-site backup replication

Backups must be copied to a storage location outside the production host. This is required because a local disk failure can otherwise destroy both the live database and the only backup copy.

Minimum requirements:

- replication to encrypted object storage or an approved remote backup system
- retention policy preserved in the remote system
- access restricted to production operators and recovery personnel only
- ownership and integrity checks performed after each replication event
- verification log stored alongside the backup metadata

Recommended replication pattern:

```bash
rsync -a --delete /var/backups/gaathasuite/ /mnt/backup-replica/gaathasuite/
# or use an approved object-store sync tool with encryption and retention rules
```

The remote copy must include:

- dump archives
- backup logs
- environment file snapshot for restore planning
- upload snapshot manifest

If an off-site target is not configured, the operator must treat the current backup state as incomplete and not claim operational readiness.

---

## 5. Uploads backup

Uploads are not stored in PostgreSQL. Back up the uploads volume at the same cadence as the database dump.

Example:

```bash
tar -czf /var/backups/gaathasuite/uploads-$(date -u +%Y%m%dT%H%M%SZ).tar.gz /var/lib/docker/volumes/gaatha_uploads/_data
```

If uploads are mounted on a host path instead of a Docker volume, back up the mounted directory itself and include a checksum manifest.

Required checks:

- confirm the uploads directory exists
- confirm it is non-empty when expected
- verify the archive is readable
- store the archive in the off-site backup target

Do not rely on DB dumps alone for recovery of user-submitted files.

---

## 6. Retention policy

Use a written retention policy that matches the business recovery objective.

Recommended default:

- 30 daily backups retained locally
- 12 monthly backups retained in the remote archive
- 1 annual full archive retained for long-term evidence
- backups older than the policy are removed only after validation, not on ad-hoc deletion

The repository script supports this with `--retention-days`:

```bash
python3 scripts/backup_database.py --retention-days 30
```

Retention deletion must log every removal event and must not delete the most recent valid backup before verification.

---

## 7. Disposable restore drill

Restore testing must never operate on the live production database. Always restore into a disposable target database.

### 7.1 Pre-checks

- confirm the dump is readable with `pg_restore --list`
- verify the target database name is not the live production name
- confirm the chosen target is isolated from application traffic

### 7.2 Restore command

```bash
python3 scripts/restore_database_test.py \
  --database-url "$DATABASE_URL" \
  --dump-path /var/backups/gaathasuite/gaatha-2026-...dump \
  --restore-db-name gaatha_restore_test_20260919T020000Z
```

### 7.3 Validation after restore

After the restore, verify:

- schema exists
- representative row counts match expectations
- key tenant records are present
- accounting totals and ownership fields remain consistent
- application health and login flow work against the restore target

A successful restore drill is evidence of recoverability, but it is not permission to restore the live database.

---

## 8. Failure alerts and verification

### 8.1 Alert conditions

The operator or automation should notify on any of the following:

- backup job exits non-zero
- backup archive is missing or zero bytes
- backup age exceeds the defined maximum threshold
- off-site replication is delayed or fails
- restore drill fails validation
- database or uploads backup is incomplete

### 8.2 Verification checks

Each backup should be validated before it is considered usable:

```bash
pg_restore --list /var/backups/gaathasuite/gaatha-*.dump | head
ls -lh /var/backups/gaathasuite
sha256sum /var/backups/gaathasuite/*.dump
```

For restore verification, run the repository helper and confirm the disposable DB is reachable:

```bash
python3 scripts/restore_database_test.py --database-url "$DATABASE_URL" --dump-path /var/backups/gaathasuite/latest.dump
```

### 8.3 Logging

All backup and restore activity must be logged with timestamps and outcomes. The repository scripts write operational logs when possible to the backup directory and to stdout/stderr.

---

## 9. Recovery procedure overview

If a production incident occurs, the operator must:

1. stop write traffic or isolate the deployment
2. confirm the latest valid backup and remote copy
3. validate backup archive integrity and upload archive integrity
4. restore PostgreSQL to a disposable database for validation
5. restore upload files to a disposable filesystem path or staging volume
6. verify application health, login, accounting, and tenant isolation against the restored data
7. only then approve a production cutover or migration plan

Do not run restore commands against the live production PostgreSQL database without a separate approved disaster-recovery approval.

---

## 10. Operational approval

This runbook is considered valid only when:

- a backup schedule is active on the host or deployment platform
- a remote backup target exists and is encrypted
- upload backup retention is documented and tested
- a disposable restore drill has succeeded in the last recovery window
- alerting is configured for failed or stale backups

If any of these are missing, Gaatha Suite remains operationally exposed and is not production-certified for full availability guarantees.
