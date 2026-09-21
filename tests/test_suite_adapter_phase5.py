import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUITE_BACKEND = ROOT / "imported" / "gaathasuite" / "gaathasuite-main" / "backend"
if str(SUITE_BACKEND) not in sys.path:
    sys.path.insert(0, str(SUITE_BACKEND))

os.environ.setdefault("SECRET_KEY", "suite-test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./suite_adapter_test.db")
os.environ.setdefault("APP_ENV", "test")

from app.main import app
from app.utils.dependencies import get_current_user
from core.platform import GaathaCoreService
from core.suite_adapter import SuiteCoreAdapter, suite_role_to_core_role


@pytest.fixture
def suite_adapter(tmp_path):
    service = GaathaCoreService(database_path=str(tmp_path / "gaathacore-suite.sqlite3"))
    return SuiteCoreAdapter(service=service)


def test_suite_role_mapping_is_explicit_and_safe():
    assert suite_role_to_core_role("superadmin") == "platform_admin"
    assert suite_role_to_core_role("orgadmin") == "organization_admin"
    assert suite_role_to_core_role("manager") == "manager"
    assert suite_role_to_core_role("lead") == "manager"
    assert suite_role_to_core_role("standard_user") == "viewer"


def test_suite_core_adapter_resolves_user_org_and_module(suite_adapter):
    core_user = suite_adapter.core.create_user(email="suite.user@example.com", username="suite_user", display_name="Suite User")
    core_org = suite_adapter.core.create_organization(name="Suite Org", slug="suite-org")
    suite_adapter.ensure_suite_mapping(suite_user_id=42, core_user_id=core_user["id"])
    suite_adapter.ensure_suite_mapping(suite_organization_id=9, core_organization_id=core_org["id"])
    suite_adapter.ensure_org_membership(suite_user_id=42, suite_organization_id=9, core_role="organization_admin")
    suite_adapter.ensure_project_scope(suite_organization_id=9, suite_project_id=77, core_project_name="Suite Project", core_project_slug="suite-project")
    suite_adapter.enable_module(organization_id=core_org["id"], project_id=suite_adapter.core.get_project_by_slug(core_org["id"], "suite-project")["id"], module_key="suite")

    identity = suite_adapter.resolve_authenticated_request(
        suite_user_id=42,
        suite_organization_id=9,
        suite_project_id=77,
        module_key="suite",
        module_permissions={"suite": ["module.read", "module.manage", "project.read"]},
    )

    assert identity["current_user"] == core_user["id"]
    assert identity["current_organization"] == core_org["id"]
    assert identity["current_module"] == "suite"
    assert "module.read" in identity["permissions"]


def test_suite_route_authentication_uses_real_fastapi_dependency():
    fake_user = type("FakeUser", (), {
        "id": 101,
        "username": "suite_route_user",
        "email": "route@example.com",
        "role": "orgadmin",
        "organization_id": 9,
        "is_active": True,
    })()

    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        from app.main import app as fastapi_app
        client = __import__("fastapi.testclient").testclient.TestClient(fastapi_app)
        response = client.get("/api/core/identity", headers={"X-Request-ID": "req-suite-123"})
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["data"]["current_user"]
        assert payload["data"]["current_module"] == "suite"
        assert payload["data"]["organization"]["id"]
    finally:
        app.dependency_overrides.clear()


def test_suite_route_rejects_cross_org_and_disabled_module(suite_adapter):
    core_user = suite_adapter.core.create_user(email="cross.org@example.com", username="cross_org", display_name="Cross Org")
    core_org_a = suite_adapter.core.create_organization(name="Org A", slug="org-a")
    core_org_b = suite_adapter.core.create_organization(name="Org B", slug="org-b")
    suite_adapter.ensure_suite_mapping(suite_user_id=12, core_user_id=core_user["id"])
    suite_adapter.ensure_suite_mapping(suite_organization_id=1, core_organization_id=core_org_a["id"])
    suite_adapter.ensure_suite_mapping(suite_organization_id=2, core_organization_id=core_org_b["id"])
    suite_adapter.ensure_org_membership(suite_user_id=12, suite_organization_id=1, core_role="organization_admin")
    suite_adapter.ensure_project_scope(suite_organization_id=1, suite_project_id=88, core_project_name="Project A", core_project_slug="project-a")

    with pytest.raises(ValueError):
        suite_adapter.resolve_authenticated_request(
            suite_user_id=12,
            suite_organization_id=2,
            suite_project_id=88,
            module_key="suite",
            module_permissions={"suite": ["project.read"]},
        )

    suite_adapter.core.set_module_access(organization_id=core_org_a["id"], project_id=suite_adapter.core.get_project_by_slug(core_org_a["id"], "project-a")["id"], module_key="suite", enabled=False)
    with pytest.raises(PermissionError):
        suite_adapter.resolve_authenticated_request(
            suite_user_id=12,
            suite_organization_id=1,
            suite_project_id=88,
            module_key="suite",
            module_permissions={"suite": ["project.read"]},
        )
