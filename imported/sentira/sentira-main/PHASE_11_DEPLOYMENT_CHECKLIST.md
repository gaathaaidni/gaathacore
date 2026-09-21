# Phase 11 Deployment Checklist: sentira.gaatha.tech

## Before deployment

- [ ] Set every required variable in an untracked production environment file: database, Redis, RabbitMQ, MinIO, JWT, camera encryption, gateway token, and legal configuration values.
- [ ] Supply reviewed values for `LEGAL_ENTITY_NAME`, `LEGAL_ENTITY_ADDRESS`, `PRIVACY_EMAIL`, `DPO_EMAIL`, `LEGAL_EMAIL`, `SUPPORT_EMAIL`, `GOVERNING_LAW`, `JURISDICTION`, and `COMPANY_REGISTRATION`. These values must describe the real operator and must not be placeholders.
- [ ] Confirm DNS `sentira.gaatha.tech` points to the VPS.
- [ ] Install Docker Compose, Nginx-compatible host firewall tooling, and certificate renewal tooling.
- [ ] Open only TCP 80/443 to the VPS; keep PostgreSQL, Redis, RabbitMQ, MinIO, MediaMTX, API, worker, and gateway ports closed externally.
- [ ] Review CPU/RAM/disk capacity and configure log rotation.

## Deploy

```bash
docker compose -f docker-compose.production.yml config
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml ps
```

- [ ] Obtain and install the certificate for `sentira.gaatha.tech`.
- [ ] Run `docker compose -f docker-compose.production.yml exec api npm run db:migrate`.
- [ ] Confirm the legal seed has created `DRAFT` documents only; do not publish seeded drafts. An authorized administrator must create or update reviewed Terms and Privacy documents through `POST /api/legal/admin/documents` and publish each reviewed document with `PATCH /api/legal/admin/documents/:id` using `{ "status": "PUBLISHED" }`.
- [ ] Verify `GET /api/legal/documents/TERMS_OF_SERVICE` and `GET /api/legal/documents/PRIVACY_POLICY` return the reviewed published documents before testing signup.
- [ ] Verify `/health` and `/ready` through the reverse proxy.
- [ ] Verify signup, login, two-camera onboarding, credential redaction, and camera limit behavior manually.

## Backup and rotation

- [ ] Schedule `scripts/backup-postgres.sh` and copy encrypted backups off-host.
- [ ] Test restore with `scripts/restore-postgres.sh` on a separate database before relying on backups.
- [ ] Rotate database, broker, object storage, JWT, camera encryption, and gateway secrets using a maintenance window.
- [ ] Revoke old credentials after all services restart successfully.

## Explicit verification boundary

This repository contains the production topology and checklist. DNS, TLS, firewall, backups, restore, certificate renewal, and VPS runtime are not verified by local repository commands and must remain pending until executed on the deployment host.
