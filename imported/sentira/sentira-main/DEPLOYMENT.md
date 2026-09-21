# Production Deployment

## Status and source of truth

The official production method is the Docker Compose stack defined by
`docker-compose.production.yml`. It builds the API and web images from the
checked-out repository, runs the supporting services on private Docker
networks, and gives ownership of public ports 80 and 443 to the Compose
`reverse-proxy` service.

The repository also contains `deploy.sh` and `VPS_DEPLOYMENT.md`. That is a
legacy PM2 plus host-Nginx deployment method retained for reference. It must
not run on the same host at the same time as the production Compose stack:
both methods claim the application processes and the public reverse-proxy
ports, but they use different API ports, environment contracts, logs, and
rollback procedures.

Production runtime verification is still pending on the VPS. This document
does not assert the current production directory, commit, image digest, or
active Nginx configuration.

## Architecture comparison

| Concern | Official Compose | Legacy PM2 script |
| --- | --- | --- |
| Public entrypoint | `reverse-proxy` container on 80/443 | Host Nginx on 80/443 |
| Web | `web:3000`, private edge network | PM2 Next.js, default `3000` |
| API | `api:4000`, private edge/internal networks | PM2 API, script default `3001` |
| API routing | `/api/` to `api:4000`, URI preserved | Host Nginx `/api/` to `localhost:3001` |
| Web routing | `/` to `web:3000` | Host Nginx `/` to `localhost:3000` |
| WebSocket | `/socket.io/` to `api:4000` | Host Nginx to `localhost:3001` |
| Environment | Compose interpolation and required production variables | `apps/api/.env.production` plus generated PM2 config |
| Migrations | API image runs TypeORM migrations before startup | No explicit migration step in `deploy.sh` |
| Rollback | Rebuild or restore a known repository/image and retain volumes | Rebuild PM2 artifacts and restore the prior checkout |

Compose service names (`api`, `web`, `reverse-proxy`, and the supporting
services) are DNS names inside Docker. They are not host processes and must
not be used as host-Nginx upstreams. The API route prefix is `/api`; health
checks are available at `/health`, `/api/health`, and `/ready`.

## Environment and data safety

Use a protected, untracked Compose environment file. Required secrets and
legal configuration values are declared in `docker-compose.production.yml`.
Do not copy development credentials from `docker-compose.yml`, print secrets,
or put secrets in the repository. Do not publish seeded legal drafts.

The API image runs migrations automatically during container startup. Treat
any command that starts or recreates the API as migration-capable and require
database backup and deployment authorization first. `synchronize` is disabled
in production.

## Non-destructive VPS diagnostic checklist

Run these only after SSH authorization. Replace `<deployment-directory>` and
`<compose-env-file>` with values discovered on the VPS; do not assume paths.

### Safe inspection commands

```bash
hostname; date -u
find /opt /srv /var/www -maxdepth 3 -name docker-compose.production.yml -print 2>/dev/null
cd <deployment-directory>
git status --short --branch
git rev-parse HEAD
git log -1 --oneline --decorate
docker compose --env-file <compose-env-file> -f docker-compose.production.yml ps
docker compose --env-file <compose-env-file> -f docker-compose.production.yml images
docker ps --no-trunc --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
pm2 status
sudo nginx -T
sudo ss -ltnp
ps aux | grep -E '[n]ode|[n]ext|[p]m2|[n]ginx'
```

Inspect the active configuration, but do not print environment files or
container environment values because they may contain secrets.

### Safe health and routing checks

```bash
docker compose --env-file <compose-env-file> -f docker-compose.production.yml exec api node -e "fetch('http://localhost:4000/health').then(async r => { console.log(r.status, await r.text()); process.exit(r.ok ? 0 : 1) }).catch(e => { console.error(e.message); process.exit(1) })"
docker compose --env-file <compose-env-file> -f docker-compose.production.yml exec api node -e "fetch('http://localhost:4000/ready').then(async r => { console.log(r.status, await r.text()); process.exit(r.ok ? 0 : 1) }).catch(e => { console.error(e.message); process.exit(1) })"
curl -fsS -D - https://sentira.gaatha.tech/health -o /tmp/sentira-health
curl -fsS -D - https://sentira.gaatha.tech/api/health -o /tmp/sentira-api-health
curl -fsS -D - https://sentira.gaatha.tech/ready -o /tmp/sentira-ready
curl -fsS -D - https://sentira.gaatha.tech/ -o /tmp/sentira-web
```

Confirm that API responses are JSON, web responses are from Next.js, and
`/api/*` does not return the frontend HTML shell. Use an invalid signup payload
only if route handling must be distinguished; it must not contain a real user
or be retried as a valid signup.

### Requires explicit deployment authorization

These commands change images or service state and are not part of diagnosis:

```bash
docker compose --env-file <compose-env-file> -f docker-compose.production.yml build api web
docker compose --env-file <compose-env-file> -f docker-compose.production.yml up -d
```

Because API startup runs migrations, do not execute these until the database
backup, target commit, image plan, rollback plan, and authorization are
explicitly confirmed.

### Restart or destructive operations

Do not run `docker compose down`, `docker compose down -v`, `docker system
prune`, database migration/revert commands, volume deletion, `pm2 restart`,
`systemctl reload/restart nginx`, or certificate changes as part of diagnosis.

## Recommended deployment sequence

1. Identify the VPS deployment directory, active process owner, and active
	Nginx configuration using the inspection checklist.
2. Stop treating any host-Nginx/PM2 stack and Compose stack as simultaneously
	authoritative; select the official Compose method for the next deployment.
3. Back up the database and verify the protected Compose environment without
	exposing its values.
4. Review the target commit and render Compose configuration.
5. With authorization, build and start the Compose stack, allowing for its
	migration behavior.
6. Verify container health, `/health`, `/api/health`, `/ready`, frontend
	routing, `/api/legal/documents`, and `/api/auth/signup` behavior.
7. Record the deployed commit, image IDs, Compose project, and rollback
	target.
