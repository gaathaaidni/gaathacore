import os

import pytest

from core.migrations.runner import CoreMigrationRunner
from core.postgres import PostgresCoreService
from core.platform import PermissionDeniedError, ResourceScopeError


DATABASE_URL = os.environ.get("CORE_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="CORE_DATABASE_URL is required for PostgreSQL-backed tests")


@pytest.fixture
def service():
    return PostgresCoreService(DATABASE_URL)


def test_postgres_migrations_are_at_head(service):
    status = CoreMigrationRunner(DATABASE_URL).status()
    assert status["pending"] == []
    assert status["head"] == "001"


def test_postgres_core_tenant_module_audit_and_usage(service):
    owner = service.create_user(email="pg-owner@example.com", username="pg-owner")
    outsider = service.create_user(email="pg-outsider@example.com", username="pg-outsider")
    limited = service.create_user(email="pg-limited@example.com", username="pg-limited")
    org = service.create_organization(name="PG Org", slug="pg-org")
    other_org = service.create_organization(name="Other PG Org", slug="other-pg-org")
    service.add_organization_membership(user_id=owner["id"], organization_id=org["id"], role="organization_owner")
    project = service.create_project(organization_id=org["id"], name="PG Project", slug="pg-project", project_type="pos")
    other_project = service.create_project(organization_id=org["id"], name="Other Project", slug="other-project", project_type="pos")
    service.add_project_membership(project_id=project["id"], user_id=owner["id"], role="project_admin")
    service.add_organization_membership(user_id=limited["id"], organization_id=org["id"], role="viewer")
    service.add_project_membership(project_id=project["id"], user_id=limited["id"], role="viewer")
    service.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="pos", enabled=True)
    service.map_pos_user(pos_user_id=901, core_user_id=owner["id"])
    service.map_pos_restaurant(pos_restaurant_id=902, core_organization_id=org["id"], core_project_id=project["id"])

    assert service.module_access_enabled(organization_id=org["id"], project_id=project["id"], module_key="pos")
    assert owner["id"] != "901"
    assert service.resolve_core_user_for_pos_user(901) == owner["id"]
    assert service.resolve_core_project_for_pos_restaurant(902) == project["id"]
    with pytest.raises(ResourceScopeError):
        service.require_scope(user_id=outsider["id"], organization_id=org["id"], project_id=project["id"], module_key="pos")
    with pytest.raises(ResourceScopeError):
        service.require_scope(user_id=owner["id"], organization_id=other_org["id"], project_id=project["id"], module_key="pos")
    with pytest.raises(PermissionDeniedError):
        service.require_scope(user_id=limited["id"], organization_id=org["id"], project_id=other_project["id"], module_key="pos")
    service.add_organization_membership(user_id=outsider["id"], organization_id=org["id"], role="viewer", status="inactive")
    with pytest.raises(ResourceScopeError):
        service.require_scope(user_id=outsider["id"], organization_id=org["id"], project_id=None)

    audit = service.log_audit(
        user_id=owner["id"], organization_id=org["id"], project_id=project["id"], module_key="pos",
        action="project.read", resource_type="project", resource_id=project["id"], success=True,
        correlation_id="pg-request-1", metadata={"test": True},
    )
    usage = service.record_usage(
        user_id=owner["id"], organization_id=org["id"], project_id=project["id"], module_key="pos",
        feature="orders", source_service="pos", quantity=2, unit="orders", idempotency_key="pg-use-1",
        metadata={"fixture": True},
    )
    assert audit["organization_id"] == org["id"]
    assert audit["correlation_id"] == "pg-request-1"
    assert audit["metadata"]["test"] is True
    assert audit["timestamp"] is not None
    assert usage["idempotency_key"] == "pg-use-1"
    assert usage["source_service"] == "pos"
    assert usage["metadata"]["fixture"] is True
    assert usage["event_timestamp"] is not None
    with pytest.raises(ResourceScopeError):
        service.log_audit(
            user_id=owner["id"], organization_id=other_org["id"], project_id=project["id"], module_key="pos",
            action="project.read", resource_type="project", resource_id=project["id"], success=True,
        )
    with pytest.raises(Exception):
        service.record_usage(
            user_id=owner["id"], organization_id=org["id"], project_id=project["id"], module_key="pos",
            feature="orders", source_service="pos", quantity=1, unit="orders", idempotency_key="pg-use-1",
        )

