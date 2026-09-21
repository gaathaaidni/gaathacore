# Phase 2.4 Implementation Plan

## 1. Findings

The Phase 2.3 report correctly identified the remaining foundation blockers. The active FastAPI runtime is authoritative, but a few genuine security and integrity issues remain in the production foundation:

- HR tenant-scoped tables are still configured with nullable `organization_id` values in the authoritative model contract.
- The legacy root config still auto-generates secrets and persists them to `.env`, which violates a strict fail-fast production policy.
- Duplicate `Asset` model definitions remain in the app and legacy code, creating ambiguity in the canonical runtime model.
- The project still contains a mixed legacy Flask surface, even though the production runtime path is FastAPI/Uvicorn.
- Full tenant/IDOR coverage across all tenant-owned CRUD endpoints remains incomplete.
- Docker network reachability between the application and its backing services remains environment-blocked in the current Codespaces/dev-container runtime.

## 2. Affected files

- `backend/app/models/hr.py`
- `backend/app/models/asset.py`
- `backend/app/models/books.py`
- `backend/app/models/__init__.py`
- `backend/app/models/user.py`
- `backend/config.py`
- `backend/migrations/versions/*.py`
- `backend/tests/test_foundation_security.py`
- `docker-compose.yml`
- `PHASE_2_3_FINAL_REPORT.md`

## 3. Proposed changes

### 3.1 HR tenant integrity

- Update the authoritative HR model definitions so `organization_id` is required for tenant-owned records.
- Add an Alembic migration to enforce non-null tenant columns only when there are no ambiguous NULL rows.
- Fail safely if legacy data cannot be assigned to an organization.

### 3.2 Secret security

- Remove the silent secret generation behavior from the legacy root config.
- Enforce required secret presence and raise a clear runtime error instead of writing fallback secrets.
- Keep this legacy path isolated from the authoritative FastAPI configuration contract.

### 3.3 Asset model consolidation

- Choose the canonical FastAPI Asset model (`app.models.asset.Asset`) as the runtime model.
- Remove ambiguous relationship binding from the duplicate `books.Asset` path.
- Preserve legacy table/data compatibility, but ensure the active runtime uses only one authoritative model.

### 3.4 Foundation test coverage

- Add regression tests for required HR tenant columns.
- Add configuration tests proving that missing secrets fail fast.
- Add integration tests for the auth/tenant foundation path where the current FastAPI contract already supports it.

## 4. Migration risks

- Existing historical data may contain NULL `organization_id` values in HR tables. These must be audited before making columns non-null.
- The duplicate `Asset` definitions may be referenced by legacy code paths that are still not in the active runtime. Any consolidation must avoid breaking historical compatibility.
- Do not remove Flask code blindly; only isolate or deprecate the legacy path.

## 5. Test strategy

- Use real PostgreSQL-backed tests where tenant and auth semantics depend on the database.
- Run migration and schema checks against an empty or clean PostgreSQL instance.
- Validate the app config fails fast when required secrets are absent.
- Run targeted pytest checks and compile checks to verify the foundation remains coherent.

## 6. Rollback considerations

- Alembic migrations are reversible only when data migration is safe and explicit; avoid destructive legacy data changes.
- Keep all patch-level changes scoped to the foundation; do not begin business-module work in this phase.
- If legacy data cannot be safely mapped, the migration should fail with a clear message rather than guessing.
