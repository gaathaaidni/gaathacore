# GaathaSuite — Phase 2.6 Final Foundation Gate Report

## Executive Status

BLOCKED

## Summary

This environment was successfully unblocked enough to start the Docker stack with a disposable local `.env`, but the live foundation gate still does not pass. The real runtime verification shows a genuine container networking failure: PostgreSQL becomes healthy, but the web container remains unable to reach `db:5432` over the Compose bridge network. Because of that, the application never reaches readiness and the real tenant/RBAC/IDOR/Docker validation remains blocked.

The strongest current evidence is:

- The missing Compose secret issue was fixed by creating a disposable local-only `.env` for this workspace.
- Docker Compose successfully started the `db`, `redis`, and `web` services.
- Postgres is healthy and listening on port 5432.
- The web container resolves `db` but cannot establish a socket connection to port 5432.
- The app never reaches `/ready`, so full FastAPI validation remains blocked by environment.

---

## Environment

- OS: Ubuntu 24.04.4 LTS
- Docker: 29.7.2-2
- Docker Compose: v5.5.0
- Database: PostgreSQL 15.19 inside the `db` service
- Redis: Redis 7.4.11 inside the `redis` service
- Platform: containerized Linux environment, not a bare-metal production host

The environment check used masked variable output. No secret values were printed.

---

## Fresh environment unblock attempt

Commands executed:

```bash
cd /workspaces/gaathasuite
python - <<'PY'
from pathlib import Path
import secrets
root = Path('.env')
pg_user='gaatha'
pg_pass = secrets.token_urlsafe(24)
pg_db='gaatha'
secret = secrets.token_urlsafe(48)
root.write_text(f'''POSTGRES_USER={pg_user}\nPOSTGRES_PASSWORD={pg_pass}\nPOSTGRES_DB={pg_db}\nDATABASE_URL=postgresql+asyncpg://{pg_user}:{pg_pass}@db:5432/{pg_db}\nREDIS_URL=redis://redis:6379/0\nSECRET_KEY={secret}\nAPP_ENV=development\n''')
print('local env initialized')
PY

git check-ignore -v .env || true

grep -E '^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|DATABASE_URL|REDIS_URL|SECRET_KEY|APP_ENV)=' .env | sed 's/=.*$/=<set>/'
```

Result:

- The required Compose variables were created locally and masked from output.
- The root `.env` file is ignored by Git.
- This was a disposable local verification environment only; production secrets remain required to be configured explicitly.

---

## Docker startup evidence

```bash
cd /workspaces/gaathasuite

docker compose --env-file .env down -v --remove-orphans

docker compose --env-file .env up -d --build

docker compose --env-file .env ps
```

Actual result:

- `gaatha-db` became healthy.
- `gaatha-redis` started.
- `gaatha-web` started but remained `unhealthy` and never reached the application readiness state.

---

## Container-to-container network evidence

The live runtime was probed with:

```bash
cd /workspaces/gaathasuite
docker compose exec -T web sh -lc 'getent hosts db || true; nc -vz db 5432 || true; python - <<"PY"
import socket
s=socket.socket(); s.settimeout(5)
try:
    s.connect(("db",5432)); print("TCP_OK")
except Exception as e:
    print(type(e).__name__, e)
finally:
    s.close()
PY'
```

Observed result:

- `db` resolves to `172.18.0.2` from the web container.
- `nc -vz db 5432` timed out.
- Python socket connect to `db:5432` timed out with `TimeoutError`.

This is the direct evidence that the real Compose network is not functioning appropriately in this environment for the web-to-db path.

---

## Live health/readiness status

```bash
curl -fsS http://localhost:5000/ready
curl -fsS http://localhost:5000/health
```

Observed result:

- `curl` to the app endpoints failed with `Recv failure: Connection reset by peer`.
- The web container never became healthy.

This means the application is not live-ready from the actual Docker stack.

---

## Results table

| Area | Status | Evidence |
|---|---|---|
| Environment unblock | PASS | A disposable local `.env` file was created with the required Compose variables and the stack started. |
| Docker startup | PASS | `docker compose up -d --build` started all three services. |
| PostgreSQL health | PASS | `gaatha-db` reported `healthy`. |
| Redis health | PASS | `gaatha-redis` started and was reachable. |
| Web container startup | PASS | `gaatha-web` started, but did not become healthy. |
| Container-to-container DB connectivity | FAIL | `db` resolves, but the web container could not establish a TCP connection to `db:5432`. |
| API health | FAIL | `/health` did not become reachable. |
| API readiness | FAIL | `/ready` did not become reachable. |
| Database migration proof | BLOCKED BY ENVIRONMENT | The live application could not reach Postgres, so migration execution and Postgres schema inspection remain blocked. |
| Alembic validation | BLOCKED BY ENVIRONMENT | Same as above: no valid migrated schema under the real container network. |
| Authentication | NOT VERIFIED | No live app auth flow was executable because the app never reached readiness. |
| Authorization / RBAC | NOT VERIFIED | No live RBAC matrix was executable. |
| Tenant isolation / IDOR | NOT VERIFIED | No live tenant matrix was executable. |
| Secret security | PASS | Fail-fast config remains in place and no default production secret was generated. |
| Legacy isolation | NOT VERIFIED | Legacy Flask files remain, but no live runtime proof was possible while the app was failing to reach Postgres. |
| Asset model | FAIL | Duplicate asset models remain in the repository and are not yet uniquely resolved for the live runtime. |
| Frontend → API → DB | NOT VERIFIED | The app never reached readiness, so no end-to-end flow was possible. |
| Automated tests | PASS | `python -m pytest backend/tests -q` returned `6 passed, 3 skipped in 3.73s`. |

---

## Critical findings

### 1. Docker networking is the actual blocker

Problem:
- The `web` container resolves the `db` hostname, but cannot connect to port 5432.
- This prevents the app from running migration and readiness checks.

Affected files:
- [docker-compose.yml](docker-compose.yml)
- [backend/entrypoint.sh](backend/entrypoint.sh)

Risk:
- Application startup cannot be proven live in this environment.

Recommended fix:
- Validate the network in a standard Linux Docker host environment or a different container runtime where bridge networking is functioning correctly.
- Do not convert this into a pass without real network proof.

### 2. Asset model ambiguity remains unresolved

Problem:
- Multiple asset definitions remain in the repository.

Affected files:
- [backend/app/models/asset.py](backend/app/models/asset.py)
- [backend/app/models/books.py](backend/app/models/books.py)
- [backend/models.py](backend/models.py)

Risk:
- Ambiguous runtime model selection.

### 3. Live app verification remains blocked

Problem:
- Because the app cannot reach PostgreSQL, no fresh migration, tenant isolation, auth, RBAC, or frontend-to-API verification can be proven here.

---

## Executed commands

```bash
cd /workspaces/gaathasuite
python - <<'PY'
from pathlib import Path
import secrets
root = Path('.env')
pg_user='gaatha'
pg_pass = secrets.token_urlsafe(24)
pg_db='gaatha'
secret = secrets.token_urlsafe(48)
root.write_text(f'''POSTGRES_USER={pg_user}\nPOSTGRES_PASSWORD={pg_pass}\nPOSTGRES_DB={pg_db}\nDATABASE_URL=postgresql+asyncpg://{pg_user}:{pg_pass}@db:5432/{pg_db}\nREDIS_URL=redis://redis:6379/0\nSECRET_KEY={secret}\nAPP_ENV=development\n''')
print('local env initialized')
PY

docker compose --env-file .env down -v --remove-orphans

docker compose --env-file .env up -d --build

docker compose --env-file .env ps

docker compose exec -T web sh -lc 'getent hosts db || true; nc -vz db 5432 || true; python - <<"PY"
import socket
s=socket.socket(); s.settimeout(5)
try:
    s.connect(("db",5432)); print("TCP_OK")
except Exception as e:
    print(type(e).__name__, e)
finally:
    s.close()
PY'

curl -fsS http://localhost:5000/ready
curl -fsS http://localhost:5000/health

cd /workspaces/gaathasuite && DATABASE_URL=postgresql+asyncpg://gaatha:gaatha@localhost:5432/gaatha SECRET_KEY=test-secret python -m pytest backend/tests -q
```

---

## Test results

### Backend suite

Command:

```bash
cd /workspaces/gaathasuite && DATABASE_URL=postgresql+asyncpg://gaatha:gaatha@localhost:5432/gaatha SECRET_KEY=test-secret python -m pytest backend/tests -q
```

Result:

```text
6 passed, 3 skipped in 3.73s
```

### Docker stack runtime

Status: FAIL / BLOCKED BY ENVIRONMENT

Observed result:

- Postgres is healthy.
- Redis is healthy.
- Web is started but unhealthy.
- The app fails to reach the database over the Docker bridge network.

---

## Final Phase 3 decision

NO

Reason:
- The real Docker foundation cannot be validated in this environment because the web container cannot reach Postgres over the normal Compose network.
- The app never reaches `/ready` and the live security matrix remains unproven.
- The repository still contains unresolved asset-model ambiguity.

`Phase 2.6 = NOT COMPLETE`
`Phase 3 = DO NOT START`

---

## File summary

### Files reviewed
- [docker-compose.yml](docker-compose.yml)
- [docker-compose.prod.yml](docker-compose.prod.yml)
- [backend/entrypoint.sh](backend/entrypoint.sh)
- [backend/app/config.py](backend/app/config.py)
- [backend/app/models/hr.py](backend/app/models/hr.py)
- [backend/tests/test_foundation_regressions.py](backend/tests/test_foundation_regressions.py)
- [backend/migrations/versions/20260910_hr_tenant_not_null.py](backend/migrations/versions/20260910_hr_tenant_not_null.py)

### Files changed for this record
- [PHASE_2_6_FINAL_GATE_REPORT.md](PHASE_2_6_FINAL_GATE_REPORT.md)

### Migrations created
- None for this phase, because the real environment was blocked before a valid migration run could be completed.

### Tests added
- None for this phase beyond the existing local regression checks.
