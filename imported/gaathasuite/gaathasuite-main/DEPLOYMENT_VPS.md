# Gaatha Suite VPS Deployment

This is the production-like controlled-beta deployment path for a normal Linux VPS. It uses Docker Compose for the application, PostgreSQL, and Redis, with host Nginx terminating HTTPS. The repository does not have access to the VPS, so DNS, certificates, firewall changes, and the final public smoke test must be performed by the operator.

## Architecture

```text
Internet -> Nginx HTTPS -> 127.0.0.1:5000 -> gaatha-web
                                      |-> db:5432 (private Docker network)
                                      |-> redis:6379 (private Docker network)
```

The production Compose file does not publish PostgreSQL or Redis. The web port is bound to loopback so it is reachable by Nginx but not directly from the public network.

## Requirements

- Linux VPS with Docker Engine and Docker Compose v2
- DNS A/AAAA record for `gaathasuite.gaatha.tech` pointing to the VPS public IP
- Firewall allowing SSH (22), HTTP (80), and HTTPS (443)
- At least 2 GB RAM recommended for the initial beta
- A private, persistent disk for Docker volumes

Do not invent or hard-code the VPS IP in this repository. Configure DNS with the actual assigned address.

## Install and start

```bash
git clone <repository-url> /opt/gaathasuite
cd /opt/gaathasuite
cp .env.vps.example .env
chmod 600 .env
${EDITOR:-vi} .env

# Check that required production variables are set and the Compose file resolves.
docker compose --env-file .env -f docker-compose.prod.yml config

docker compose --env-file .env -f docker-compose.prod.yml up -d --build
docker compose --env-file .env -f docker-compose.prod.yml ps
```

Startup waits for PostgreSQL, runs `alembic upgrade head`, and only then starts FastAPI. It does not drop or recreate production tables.

Verify locally on the VPS:

```bash
curl -i http://127.0.0.1:5000/health
curl -i http://127.0.0.1:5000/ready
docker compose --env-file .env -f docker-compose.prod.yml exec web sh -lc 'cd /app/backend && alembic current'
```

## Nginx and HTTPS

1. Create the DNS A/AAAA record for `gaathasuite.gaatha.tech`.
2. Install Nginx and Certbot using the VPS distribution packages.
3. Copy `deploy/nginx/gaathasuite.conf` to `/etc/nginx/sites-available/gaathasuite.gaatha.tech`.
4. Enable it, validate Nginx, and obtain the certificate:

```bash
sudo ln -s /etc/nginx/sites-available/gaathasuite.gaatha.tech /etc/nginx/sites-enabled/gaathasuite.gaatha.tech
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d gaathasuite.gaatha.tech
```

After TLS is active, verify:

```bash
curl -i https://gaathasuite.gaatha.tech/health
curl -i https://gaathasuite.gaatha.tech/ready
```

Do not expose port 5000 publicly. Nginx should be the public entry point.

## Firewall

Apply firewall rules only on the intended VPS. A typical posture is:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Do not allow 5432 or 6379 from the Internet.

## Backups

The PostgreSQL volume is `gaatha_postgres_data`; uploads are in `gaatha_uploads`. A database dump is not a substitute for backing up required uploaded files.

Create a timestamped database backup on protected storage:

```bash
mkdir -p /var/backups/gaathasuite
cd /opt/gaathasuite
set -a; . ./.env; set +a
docker compose --env-file .env -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom \
  > "/var/backups/gaathasuite/db-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Verify a dump without modifying the live database:

```bash
pg_restore --list /var/backups/gaathasuite/db-*.dump | head
```

Restore only during a planned maintenance window into an isolated or explicitly approved target database:

```bash
cat backup.dump | docker compose --env-file .env -f docker-compose.prod.yml exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists
```

Copy the `gaatha_uploads` Docker volume or its mounted storage with the database backup. No off-site or scheduled backup service is configured by this repository; the operator must provide retention, encryption, and off-site replication.

## Updates and rollback

```bash
cd /opt/gaathasuite
cp .env /var/backups/gaathasuite/env-$(date -u +%Y%m%dT%H%M%SZ)
# Take a database and uploads backup first.
git pull --ff-only
docker compose --env-file .env -f docker-compose.prod.yml config
docker compose --env-file .env -f docker-compose.prod.yml up -d --build
docker compose --env-file .env -f docker-compose.prod.yml ps
curl -i https://gaathasuite.gaatha.tech/health
curl -i https://gaathasuite.gaatha.tech/ready
```

For rollback, stop at the last known-good commit, rebuild that image, and restore the database only if the migration history requires it. Do not downgrade migrations blindly; inspect the migration and restore backup data in a maintenance window.

## Restart and troubleshooting

```bash
docker compose --env-file .env -f docker-compose.prod.yml restart web

docker compose --env-file .env -f docker-compose.prod.yml restart redis

docker compose --env-file .env -f docker-compose.prod.yml restart db

docker compose --env-file .env -f docker-compose.prod.yml logs --tail=200 web db redis
```

- Database unavailable: check `docker compose ps`, PostgreSQL health, disk space, and the `POSTGRES_*` values. The app must use `db:5432`, not `host.docker.internal`.
- Migration failure: stop exposure through Nginx, inspect the current Alembic revision and backup, then fix or roll back deliberately. Never delete the volume to bypass a migration.
- Web unhealthy: inspect web logs and query `/ready`; readiness failures should be treated as a deployment issue.
- Redis unavailable: inspect the Redis health check and logs. Redis is not the primary data store; do not recreate PostgreSQL because Redis is unavailable.
- HTTPS issue: verify DNS, `nginx -t`, certificate paths, and firewall ports 80/443.

## Controlled-beta limitations

This deployment path does not make the product fully production-certified. MFA, rate limiting, complete RBAC/IDOR coverage, full business workflow E2E coverage, legal review, and scheduled off-site backups remain operational/product limitations. The deployment should be opened only as a controlled beta after the operator completes the public HTTPS and smoke tests.
