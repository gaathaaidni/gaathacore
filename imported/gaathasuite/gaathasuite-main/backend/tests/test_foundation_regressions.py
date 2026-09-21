import os
import sys

import pytest
from sqlalchemy.engine import make_url

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

requires_test_database = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL must point to an isolated PostgreSQL database",
)


@pytest.mark.parametrize(
    "model_name",
    [
        "Department",
        "Employee",
        "Payslip",
        "AttendanceRecord",
        "PerformanceReview",
    ],
)
@requires_test_database
def test_hr_tenant_columns_are_not_nullable(model_name):
    from app.models.hr import (
        AttendanceRecord,
        Department,
        Employee,
        Payslip,
        PerformanceReview,
    )

    model_map = {
        "Department": Department,
        "Employee": Employee,
        "Payslip": Payslip,
        "AttendanceRecord": AttendanceRecord,
        "PerformanceReview": PerformanceReview,
    }
    model = model_map[model_name]
    column = model.__table__.c.organization_id
    assert column.nullable is False, f"{model_name}.organization_id must be NOT NULL"


@requires_test_database
def test_runtime_asset_model_is_single_authoritative_model():
    from app.models.asset import Asset as RuntimeAsset
    from app.models.user import User
    import app.models.books as books_module

    user_rel = User.__mapper__.relationships["assets"]
    legacy_asset = books_module.Asset

    assert RuntimeAsset.__tablename__ == "assets"
    assert legacy_asset.__tablename__ == "asset"
    assert legacy_asset is not RuntimeAsset
    assert user_rel.mapper.class_ is RuntimeAsset
    assert user_rel.argument == "app.models.asset.Asset"


@requires_test_database
def test_test_database_driver_split_is_async_and_isolated():
    from app.db import DATABASE_URL
    from conftest import get_test_sync_database_url

    assert make_url(DATABASE_URL).drivername == "postgresql+asyncpg"
    assert make_url(get_test_sync_database_url()).drivername == "postgresql+psycopg2"
    assert make_url(DATABASE_URL).database == "gaatha_migration_test"
    assert make_url(get_test_sync_database_url()).database == "gaatha_migration_test"


@requires_test_database
def test_public_urls_are_configurable_and_security_headers_are_strict(monkeypatch):
    import importlib
    from fastapi.testclient import TestClient

    monkeypatch.setenv("BASE_URL", "https://gaathasuite.example.com")
    import app.config as config_module
    importlib.reload(config_module)

    assert config_module.Config.BASE_URL == "https://gaathasuite.example.com"
    assert config_module.Config.public_url("/auth/login") == "https://gaathasuite.example.com/auth/login"

    from app.main import app
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("strict-transport-security", "").lower().startswith("max-age=")


def test_superadmin_can_create_leads_without_org_context(api_client):
    import asyncio
    from sqlalchemy import select

    from app.db import AsyncSessionLocal
    from app.models.crm import Lead
    from app.models.user import User

    async def seed_user():
        async with AsyncSessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == "superadmin@example.com"))
            if user is None:
                user = User(
                    username="superadmin",
                    email="superadmin@example.com",
                    role="superadmin",
                    organization_id=None,
                    is_active=True,
                )
                user.set_password("SuperPass123!")
                db.add(user)
                await db.commit()
                await db.refresh(user)

    asyncio.run(seed_user())

    login_response = api_client.post(
        "/auth/login",
        json={"username": "superadmin@example.com", "password": "SuperPass123!"},
    )
    assert login_response.status_code == 200, login_response.text

    token = login_response.json()["access_token"]
    lead_response = api_client.post(
        "/crm/api/leads",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Fallback org lead",
            "company": "Fallback Org",
            "contact_email": "fallback@example.com",
            "source": "Web",
        },
    )
    assert lead_response.status_code == 201, lead_response.text

    created = lead_response.json()
    assert created["name"] == "Fallback org lead"

    async def assert_org_context():
        async with AsyncSessionLocal() as db:
            saved = await db.get(Lead, created["id"])
            assert saved is not None
            assert saved.organization_id is not None

    asyncio.run(assert_org_context())


def test_legacy_backend_config_fails_fast_without_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    import importlib

    sys.modules.pop("config", None)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        importlib.import_module("config")
