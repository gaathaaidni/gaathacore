#!/usr/bin/env bash
# ==============================================================================
# GaathaCore Phase 6 — Production Secret Rotation & Safety Validation Script
# Target Host: VPS srv1520753 (31.97.230.208)
# Directory: /root/gaathacore
# ==============================================================================
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/root/gaathacore}"
cd "$WORKSPACE_DIR"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
BACKUP_DIR="${WORKSPACE_DIR}/backups/secret_rotation_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

echo "======================================================================="
echo "=== Phase 6: Production Secret Rotation & Safety Gate Execution     ==="
echo "=== Timestamp: ${TIMESTAMP} UTC                                     ==="
echo "======================================================================="

# ------------------------------------------------------------------------------
# 1. FINAL PRE-ROTATION SAFETY CHECK & BASELINE VALIDATION
# ------------------------------------------------------------------------------
echo -e "\n[Step 1/6] Performing Pre-Rotation Safety Checks & Health Probes..."

# Check Docker Compose status
echo "-> Checking Docker Compose service status..."
docker compose ps

# Pre-rotation HTTP Probes
echo "-> Verifying pre-rotation endpoint health..."
curl -fsS -o /dev/null -w "  - Apex Directory (gaatha.tech): %{http_code}\n" https://gaatha.tech/
curl -fsS -o /dev/null -w "  - Sentira API (/sentira/api/health): %{http_code}\n" https://gaatha.tech/sentira/api/health
curl -fsS -o /dev/null -w "  - Gaatha POS (/pos/health): %{http_code}\n" https://gaatha.tech/pos/health
curl -fsS -o /dev/null -w "  - Gaatha Suite (/suite/): %{http_code}\n" https://gaatha.tech/suite/
curl -s -o /dev/null -w "  - PostPilot Gated Probe (/postpilot): %{http_code} (expect 404)\n" https://gaatha.tech/postpilot

# ------------------------------------------------------------------------------
# 2. FULL PRE-ROTATION BACKUP CAPTURE (Configuration & Databases)
# ------------------------------------------------------------------------------
echo -e "\n[Step 2/6] Capturing Pre-Rotation State & Database Snapshots..."

# Backup .env and docker-compose.yml
echo "-> Backing up .env to ${BACKUP_DIR}/pre_rotation.env.bak"
cp .env "${BACKUP_DIR}/pre_rotation.env.bak"
cp docker-compose.yml "${BACKUP_DIR}/pre_rotation.docker-compose.yml.bak"
chmod 600 "${BACKUP_DIR}/pre_rotation.env.bak"

# Source current .env for database credentials
set -a
# shellcheck disable=SC1091
source .env
set +a

# Database Snapshots (custom-format dumps)
echo "-> Dumping 5 PostgreSQL databases into ${BACKUP_DIR}/..."
docker compose exec -T postgres pg_dump -U postgres -d gaathacore_core --format=custom --no-owner > "${BACKUP_DIR}/gaathacore_core_${TIMESTAMP}.dump"
docker compose exec -T postgres pg_dump -U postgres -d gaathasuite --format=custom --no-owner > "${BACKUP_DIR}/gaathasuite_${TIMESTAMP}.dump"
docker compose exec -T postgres pg_dump -U postgres -d gaathapos --format=custom --no-owner > "${BACKUP_DIR}/gaathapos_${TIMESTAMP}.dump"
docker compose exec -T postgres pg_dump -U postgres -d sentira --format=custom --no-owner > "${BACKUP_DIR}/sentira_${TIMESTAMP}.dump"
docker compose exec -T postgres pg_dump -U postgres -d postpilot --format=custom --no-owner > "${BACKUP_DIR}/postpilot_${TIMESTAMP}.dump"
echo "-> Verified: All 5 database snapshots written successfully."

# ------------------------------------------------------------------------------
# 3. CAMERA ENCRYPTION KEY STATE & RE-ENCRYPTION PATH VALIDATION
# ------------------------------------------------------------------------------
echo -e "\n[Step 3/6] Inspecting Sentira Camera Credential Database State..."

CAMERA_AUDIT=$(docker compose exec -T postgres psql -U postgres -d sentira -tAc '
    SELECT 
        COUNT(*) || ":" || 
        COUNT("passwordEncrypted") 
    FROM cameras;
' 2>/dev/null || echo "0:0")

TOTAL_CAMERAS=$(echo "$CAMERA_AUDIT" | cut -d':' -f1 | tr -d ' ')
ENCRYPTED_PW_CAMERAS=$(echo "$CAMERA_AUDIT" | cut -d':' -f2 | tr -d ' ')

echo "-> Sentira Camera Inspection:"
echo "   - Total camera records in DB: ${TOTAL_CAMERAS}"
echo "   - Cameras with encrypted passwords: ${ENCRYPTED_PW_CAMERAS}"

if [ "${ENCRYPTED_PW_CAMERAS}" -gt 0 ]; then
    echo "⚠️  ACTIVE ENCRYPTED CAMERAS DETECTED (${ENCRYPTED_PW_CAMERAS})."
    echo "   Enforcing strict user mandate: HOLDING SENTIRA_CAMERA_CREDENTIAL_ENCRYPTION_KEY."
    echo "   Camera key will NOT be modified to preserve credential integrity."
    HOLD_CAMERA_KEY=1
else
    echo "✅ Zero active encrypted camera credentials found in database."
    echo "   Enforcing strict safety requirement: Keeping SENTIRA_CAMERA_CREDENTIAL_ENCRYPTION_KEY held and verified."
    HOLD_CAMERA_KEY=1
fi

# ------------------------------------------------------------------------------
# 4. GENERATE HIGH-ENTROPY SECRETS
# ------------------------------------------------------------------------------
echo -e "\n[Step 4/6] Generating High-Entropy Secrets & Synchronizing Engines..."

# Helper for secure tokens
gen_hex() { openssl rand -hex 32; }
gen_urlsafe() { python3 -c "import secrets; print(secrets.token_urlsafe(48))"; }
gen_alphanumeric() { python3 -c "import secrets, string; alphabet = string.ascii_letters + string.digits; print(''.join(secrets.choice(alphabet) for _ in range(32)))"; }

NEW_CORE_POSTGRES_PASSWORD=$(gen_alphanumeric)
NEW_SUITE_POSTGRES_PASSWORD=$(gen_alphanumeric)
NEW_POS_POSTGRES_PASSWORD=$(gen_alphanumeric)
NEW_SENTIRA_POSTGRES_PASSWORD=$(gen_alphanumeric)
NEW_POSTPILOT_POSTGRES_PASSWORD=$(gen_alphanumeric)

NEW_SUITE_SECRET_KEY=$(gen_urlsafe)
NEW_POS_SECRET_KEY=$(gen_hex)
NEW_SENTIRA_JWT_SECRET=$(gen_urlsafe)

NEW_SENTIRA_STREAM_GATEWAY_INTERNAL_TOKEN=$(gen_hex)
NEW_SENTIRA_STREAM_GATEWAY_AUTH_SECRET=$(gen_hex)
NEW_SENTIRA_AI_WORKER_INGEST_TOKEN=$(gen_hex)

NEW_SENTIRA_REDIS_PASSWORD=$(gen_alphanumeric)
NEW_SENTIRA_RABBITMQ_PASSWORD=$(gen_alphanumeric)
NEW_SENTIRA_MINIO_ROOT_PASSWORD=$(gen_alphanumeric)

# 4A. Update PostgreSQL in-engine credentials
echo "-> Synchronizing in-engine PostgreSQL user passwords..."
docker compose exec -T postgres psql -U postgres -c "ALTER USER \"${CORE_POSTGRES_USER}\" WITH PASSWORD '${NEW_CORE_POSTGRES_PASSWORD}';"
docker compose exec -T postgres psql -U postgres -c "ALTER USER \"${SUITE_POSTGRES_USER}\" WITH PASSWORD '${NEW_SUITE_POSTGRES_PASSWORD}';"
docker compose exec -T postgres psql -U postgres -c "ALTER USER \"${POS_POSTGRES_USER}\" WITH PASSWORD '${NEW_POS_POSTGRES_PASSWORD}';"
docker compose exec -T postgres psql -U postgres -c "ALTER USER \"${SENTIRA_POSTGRES_USER}\" WITH PASSWORD '${NEW_SENTIRA_POSTGRES_PASSWORD}';"
docker compose exec -T postgres psql -U postgres -c "ALTER USER \"${POSTPILOT_POSTGRES_USER}\" WITH PASSWORD '${NEW_POSTPILOT_POSTGRES_PASSWORD}';"
echo "-> PostgreSQL role passwords successfully updated in-engine."

# 4B. Update RabbitMQ in-engine credentials
echo "-> Synchronizing in-engine RabbitMQ user passwords..."
docker compose exec -T sentira_rabbitmq rabbitmqctl change_password "${SENTIRA_RABBITMQ_USER}" "${NEW_SENTIRA_RABBITMQ_PASSWORD}"
echo "-> RabbitMQ user password successfully updated in-engine."

# 4C. Update .env atomically
echo "-> Writing new rotated secrets to .env..."
cp .env .env.tmp

update_env_var() {
    local key="$1"
    local val="$2"
    if grep -q "^${key}=" .env.tmp; then
        sed -i "s|^${key}=.*|${key}=${val}|" .env.tmp
    else
        echo "${key}=${val}" >> .env.tmp
    fi
}

update_env_var "CORE_POSTGRES_PASSWORD" "${NEW_CORE_POSTGRES_PASSWORD}"
update_env_var "SUITE_POSTGRES_PASSWORD" "${NEW_SUITE_POSTGRES_PASSWORD}"
update_env_var "POS_POSTGRES_PASSWORD" "${NEW_POS_POSTGRES_PASSWORD}"
update_env_var "SENTIRA_POSTGRES_PASSWORD" "${NEW_SENTIRA_POSTGRES_PASSWORD}"
update_env_var "POSTPILOT_POSTGRES_PASSWORD" "${NEW_POSTPILOT_POSTGRES_PASSWORD}"

update_env_var "SUITE_SECRET_KEY" "${NEW_SUITE_SECRET_KEY}"
update_env_var "POS_SECRET_KEY" "${NEW_POS_SECRET_KEY}"
update_env_var "SENTIRA_JWT_SECRET" "${NEW_SENTIRA_JWT_SECRET}"

update_env_var "SENTIRA_STREAM_GATEWAY_INTERNAL_TOKEN" "${NEW_SENTIRA_STREAM_GATEWAY_INTERNAL_TOKEN}"
update_env_var "SENTIRA_STREAM_GATEWAY_AUTH_SECRET" "${NEW_SENTIRA_STREAM_GATEWAY_AUTH_SECRET}"
update_env_var "SENTIRA_AI_WORKER_INGEST_TOKEN" "${NEW_SENTIRA_AI_WORKER_INGEST_TOKEN}"

update_env_var "SENTIRA_REDIS_PASSWORD" "${NEW_SENTIRA_REDIS_PASSWORD}"
update_env_var "SENTIRA_RABBITMQ_PASSWORD" "${NEW_SENTIRA_RABBITMQ_PASSWORD}"
update_env_var "SENTIRA_MINIO_ROOT_PASSWORD" "${NEW_SENTIRA_MINIO_ROOT_PASSWORD}"

# Note: SENTIRA_CAMERA_CREDENTIAL_ENCRYPTION_KEY is intentionally PRESERVED and untouched.

mv .env.tmp .env
chmod 600 .env
echo "-> .env updated with strict permissions (600)."

# ------------------------------------------------------------------------------
# 5. COORDINATED SERVICE RESTARTS
# ------------------------------------------------------------------------------
echo -e "\n[Step 5/6] Executing Coordinated Service Restarts in Dependency Order..."

echo "-> Restoring/Restarting Gaatha POS cluster (web, worker, beat)..."
docker compose up -d --force-recreate pos_web pos_worker pos_beat

echo "-> Restarting Gaatha Suite web..."
docker compose up -d --force-recreate suite_web

echo "-> Restarting Sentira infrastructure (Redis, MinIO)..."
docker compose up -d --force-recreate sentira_redis sentira_minio

echo "-> Restarting Sentira API..."
docker compose up -d --force-recreate sentira_api

echo "-> Restarting Sentira Gateway, AI Worker, and Web UI..."
docker compose up -d --force-recreate sentira_stream_gateway sentira_ai_worker sentira_web

echo "-> Restarting PostPilot (gated internal)..."
docker compose up -d --force-recreate postpilot_web

echo "-> Waiting 15 seconds for services to achieve full readiness..."
sleep 15

# ------------------------------------------------------------------------------
# 6. POST-ROTATION LIVE VALIDATION & AUTOMATED TEST SUITE
# ------------------------------------------------------------------------------
echo -e "\n[Step 6/6] Executing Post-Rotation Smoke Tests & Automated Suite..."

echo "-> Container Health Status:"
docker compose ps

echo -e "\n-> Probing Live Endpoints Post-Rotation:"
curl -fsS -o /dev/null -w "  - Apex Directory (gaatha.tech): %{http_code}\n" https://gaatha.tech/
curl -fsS -o /dev/null -w "  - Sentira API (/sentira/api/health): %{http_code}\n" https://gaatha.tech/sentira/api/health
curl -fsS -o /dev/null -w "  - Sentira Web UI (/sentira): %{http_code}\n" https://gaatha.tech/sentira
curl -fsS -o /dev/null -w "  - Gaatha POS Health (/pos/health): %{http_code}\n" https://gaatha.tech/pos/health
curl -fsS -o /dev/null -w "  - Gaatha POS Web UI (/pos/): %{http_code}\n" https://gaatha.tech/pos/
curl -fsS -o /dev/null -w "  - Gaatha Suite Web UI (/suite/): %{http_code}\n" https://gaatha.tech/suite/
curl -fsS -o /dev/null -w "  - Gaatha Suite Static Assets (/static/dist/icon.png): %{http_code}\n" https://gaatha.tech/static/dist/icon.png
curl -s -o /dev/null -w "  - PostPilot Gated Check (/postpilot): %{http_code} (expect 404)\n" https://gaatha.tech/postpilot
curl -fsS -o /dev/null -w "  - Co-hosted Phoenix (phoenix.gaatha.tech): %{http_code}\n" https://phoenix.gaatha.tech
curl -fsS -o /dev/null -w "  - Co-hosted CCT (cct.gaatha.tech): %{http_code}\n" https://cct.gaatha.tech

echo -e "\n-> Executing 24 Security & Isolation Pytest Suite:"
python3 -m pytest -p no:anyio -v tests/test_core_phase4.py tests/test_pos_adapter_phase6.py tests/test_public_entry.py

echo -e "\n======================================================================="
echo "=== Phase 6 Secret Rotation COMPLETED SUCCESSFULLY                  ==="
echo "======================================================================="
