# Backup and Restore

**Status:** OPERATOR PROCEDURE / AUTOMATION NOT VERIFIED.

The Compose file persists PostgreSQL and uploads in volumes, but repository evidence does not prove automated backups.

1. Schedule encrypted PostgreSQL dumps and retain them according to a confirmed business policy.
2. Back up the uploads volume and deployment configuration separately.
3. Store backups outside the production host with restricted access.
4. Verify backups by restoring to an isolated PostgreSQL and file volume.
5. Record restore duration and integrity results.
6. For recovery, stop writes, restore database and files, apply reviewed migrations, start services, and verify `/ready`, login, and critical workflows.

Frequency, retention, RPO, and RTO require business confirmation.
