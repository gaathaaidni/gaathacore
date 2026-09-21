#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[FAIL] DATABASE_URL is not set" >&2
  exit 1
fi

if [[ -z "${SECRET_KEY:-}" ]]; then
  echo "[FAIL] SECRET_KEY is not set" >&2
  exit 1
fi

echo "[1/10] Python compile"
python -m compileall -q "$BACKEND_DIR"

echo "[2/10] Backend tests"
(cd "$BACKEND_DIR" && pytest -q)

echo "[3/10] Frontend build"
(cd "$FRONTEND_DIR" && npm run build)

echo "[4/10] Git diff hygiene"
(cd "$ROOT_DIR" && git diff --check)

echo "[5/10] Docker config"
(cd "$ROOT_DIR" && docker compose config >/dev/null)

echo "[6/10] Migration head"
(cd "$BACKEND_DIR" && python -m alembic -c migrations/alembic.ini upgrade head)

echo "[7/10] Canonical schema check"
# env.py applies the canonical comparison contract: legacy compatibility table
# drift is intentional, while active-table drift makes this command fail.
(cd "$BACKEND_DIR" && python -m alembic -c migrations/alembic.ini check)
echo "CANONICAL_SCHEMA_CHECK=PASS"
echo "LEGACY_COMPATIBILITY_DRIFT=INTENTIONAL"

echo "[8/10] Health endpoints"
(cd "$BACKEND_DIR" && python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    health = client.get('/health')
    ready = client.get('/ready')
    print(f'health={health.status_code}')
    print(f'ready={ready.status_code}')
    if health.status_code != 200:
        raise SystemExit(1)
    if ready.status_code not in (200, 503):
        raise SystemExit(1)
PY
)

echo "[9/10] Mandatory security gates"
if [[ ! -f "$BACKEND_DIR/tests/test_auth_tenant_foundation.py" ]]; then
  echo "[FAIL] Tenant security test file is missing" >&2
  exit 1
fi
if [[ ! -f "$BACKEND_DIR/tests/test_foundation_regressions.py" ]]; then
  echo "[FAIL] RBAC/security regression file is missing" >&2
  exit 1
fi

# Keep the gate honest: the repository still needs explicit cross-tenant/accounting coverage.
# If the Phase 1 security suite is not present, fail the gate so it does not claim green.
if ! grep -q "cross\|organization.*B\|tenant" "$BACKEND_DIR/tests/test_auth_tenant_foundation.py" 2>/dev/null; then
  echo "[FAIL] Tenant isolation regression coverage is incomplete" >&2
  exit 1
fi

if ! grep -q "superadmin\|organization.*another\|403" "$BACKEND_DIR/tests/test_foundation_regressions.py" 2>/dev/null; then
  echo "[FAIL] RBAC/security regression coverage is incomplete" >&2
  exit 1
fi

echo "[10/10] Release gate complete: repository is still YELLOW until Phase 1 accounting and tenant security coverage are fully proven"
