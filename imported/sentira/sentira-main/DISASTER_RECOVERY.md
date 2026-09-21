# Disaster Recovery

## IMPLEMENTED — NOT VERIFIED
`POSTGRES_URL=... scripts/backup-postgres.sh` creates a custom `pg_dump`. Restore with `POSTGRES_URL=... scripts/restore-postgres.sh backups/file.dump`. Verify with application health and tenant row counts. Evidence/MinIO backup, RabbitMQ quorum recovery, and Redis recovery are future operational runbook work. RPO/RTO are deployment-specific and have not been validated.
