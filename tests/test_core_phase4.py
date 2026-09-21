import uuid

import pytest

from core.platform import (
    CoreContext,
    GaathaCoreService,
    PermissionDeniedError,
    ResourceScopeError,
)


@pytest.fixture
def service(tmp_path):
    db_path = tmp_path / "gaathacore-core.sqlite3"
    return GaathaCoreService(database_path=str(db_path))


def _make_user(service, email="owner@example.com", username="owner", display_name="Owner"):
    return service.create_user(email=email, username=username, display_name=display_name, status="active")


def test_authenticated_user_can_resolve_identity(service):
    user = _make_user(service)
    org = service.create_organization(name="Acme", slug="acme")
    service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="organization_owner", status="active")

    result = service.resolve_identity(user_id=user["id"], organization_id=org["id"])

    assert result["user"]["id"] == user["id"]
    assert result["organization"]["id"] == org["id"]
    assert result["membership"]["role"] == "organization_owner"


def test_unknown_user_denied(service):
    with pytest.raises(PermissionDeniedError):
        service.resolve_identity(user_id="missing-user")


def test_disabled_user_denied(service):
    user = service.create_user(email="disabled@example.com", username="disabled", display_name="Disabled", status="disabled")

    with pytest.raises(PermissionDeniedError):
        service.resolve_identity(user_id=user["id"])


def test_organization_creation_and_membership(service):
    user = _make_user(service)
    org = service.create_organization(name="Plain Org", slug="plain-org")
    membership = service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="organization_admin", status="active")

    assert membership["role"] == "organization_admin"
    assert service.get_organization_memberships(org["id"])[0]["user_id"] == user["id"]


def test_organization_isolation(service):
    user = _make_user(service)
    org_a = service.create_organization(name="Org A", slug="org-a")
    org_b = service.create_organization(name="Org B", slug="org-b")
    service.add_organization_membership(user_id=user["id"], organization_id=org_a["id"], role="organization_owner", status="active")

    with pytest.raises(ResourceScopeError):
        service.require_scope(user_id=user["id"], organization_id=org_b["id"], project_id=None)


def test_project_belongs_to_organization(service):
    user = _make_user(service)
    org = service.create_organization(name="Alpha", slug="alpha")
    service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="organization_owner", status="active")
    project = service.create_project(organization_id=org["id"], name="Main project", slug="main-project", project_type="business")
    other_org = service.create_organization(name="Beta", slug="beta")

    assert service.get_project(project["id"])["organization_id"] == org["id"]
    with pytest.raises(ResourceScopeError):
        service.require_scope(user_id=user["id"], organization_id=other_org["id"], project_id=project["id"])


def test_project_membership_management(service):
    actor = _make_user(service, email="admin@example.com", username="project-admin", display_name="Project Admin")
    target = _make_user(service, email="staff@example.com", username="staff-member", display_name="Staff Member")
    org = service.create_organization(name="Ops", slug="ops")
    service.add_organization_membership(user_id=actor["id"], organization_id=org["id"], role="organization_owner", status="active")
    project = service.create_project(organization_id=org["id"], name="Ops App", slug="ops-app", project_type="business")
    service.add_project_membership(project_id=project["id"], user_id=actor["id"], role="project_admin", status="active")

    service.add_project_membership(project_id=project["id"], user_id=target["id"], role="staff", status="active")

    assert service.get_project_memberships(project["id"])[1]["user_id"] == target["id"]

    viewer = _make_user(service, email="viewer@example.com", username="viewer-member", display_name="Viewer")
    service.add_organization_membership(user_id=viewer["id"], organization_id=org["id"], role="viewer", status="active")
    with pytest.raises(PermissionDeniedError):
        service.ensure_permission(user_id=viewer["id"], organization_id=org["id"], project_id=project["id"], permission="project.members.manage")


def test_role_permissions_map(service):
    roles = {
        "platform_admin": "organization.read",
        "organization_owner": "organization.members.manage",
        "organization_admin": "project.update",
        "project_admin": "module.manage",
        "manager": "module.read",
        "staff": "project.read",
        "viewer": "usage.read",
    }

    for role, permission in roles.items():
        assert permission in service.role_permissions(role)


def test_enabled_module_access(service):
    user = _make_user(service, email="suite-owner@example.com", username="suite-owner", display_name="Suite Owner")
    org = service.create_organization(name="Suite Org", slug="suite-org")
    service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="organization_owner", status="active")
    project = service.create_project(organization_id=org["id"], name="Suite Project", slug="suite-project", project_type="business")
    service.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="suite", enabled=True)

    ctx = service.resolve_context(user_id=user["id"], organization_id=org["id"], project_id=project["id"], module_key="suite")
    assert ctx.module == "suite"
    assert ctx.current_organization == org["id"]
    assert service.module_access_enabled(organization_id=org["id"], project_id=project["id"], module_key="suite") is True


def test_disabled_module_denied(service):
    user = _make_user(service, email="blocked@example.com", username="blocked-user", display_name="Blocked")
    org = service.create_organization(name="Blocked Org", slug="blocked-org")
    service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="organization_owner", status="active")
    project = service.create_project(organization_id=org["id"], name="Blocked Project", slug="blocked-project", project_type="business")
    service.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="postpilot", enabled=False)

    with pytest.raises(PermissionDeniedError):
        service.resolve_context(user_id=user["id"], organization_id=org["id"], project_id=project["id"], module_key="postpilot")


def test_unauthorized_project_cannot_access_module(service):
    owner = _make_user(service, email="owner-b@example.com", username="owner-b", display_name="Owner B")
    org_a = service.create_organization(name="A Org", slug="a-org")
    org_b = service.create_organization(name="B Org", slug="b-org")
    service.add_organization_membership(user_id=owner["id"], organization_id=org_a["id"], role="organization_owner", status="active")
    project = service.create_project(organization_id=org_a["id"], name="A Project", slug="a-project", project_type="business")
    service.set_module_access(organization_id=org_a["id"], project_id=project["id"], module_key="sentira", enabled=True)

    with pytest.raises(ResourceScopeError):
        service.require_scope(user_id=owner["id"], organization_id=org_b["id"], project_id=project["id"], module_key="sentira")


def test_admin_mutation_produces_audit_event(service):
    user = _make_user(service, email="audit-owner@example.com", username="audit-owner", display_name="Audit Owner")
    org = service.create_organization(name="Audit Org", slug="audit-org")
    service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="organization_owner", status="active")

    audit_event = service.log_audit(
        user_id=user["id"],
        organization_id=org["id"],
        project_id=None,
        module_key="suite",
        action="organization.members.manage",
        resource_type="organization_membership",
        resource_id="membership-123",
        success=True,
        correlation_id="req-100",
        metadata={"target_user": "staff-user"},
    )

    assert audit_event["success"] is True
    assert audit_event["organization_id"] == org["id"]
    assert audit_event["module"] == "suite"
    assert audit_event["correlation_id"] == "req-100"


def test_usage_context_resolves_and_rejects_cross_tenant(service):
    user = _make_user(service, email="usage-user@example.com", username="usage-user", display_name="Usage User")
    org = service.create_organization(name="Usage Org", slug="usage-org")
    service.add_organization_membership(user_id=user["id"], organization_id=org["id"], role="project_admin", status="active")
    project = service.create_project(organization_id=org["id"], name="Usage Project", slug="usage-project", project_type="pos")
    service.add_project_membership(project_id=project["id"], user_id=user["id"], role="project_admin", status="active")
    service.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="pos", enabled=True)

    usage = service.record_usage(
        user_id=user["id"],
        organization_id=org["id"],
        project_id=project["id"],
        module_key="pos",
        feature="transactions",
        source_service="pos",
        quantity=3,
        unit="orders",
        correlation_id="usage-1",
    )

    assert usage["organization_id"] == org["id"]
    assert usage["module_key"] == "pos"

    other_org = service.create_organization(name="Other Org", slug="other-org")
    with pytest.raises(ResourceScopeError):
        service.record_usage(
            user_id=user["id"],
            organization_id=other_org["id"],
            project_id=project["id"],
            module_key="pos",
            feature="transactions",
            source_service="pos",
            quantity=1,
            unit="orders",
            correlation_id="usage-2",
        )


def test_core_api_envelope_shape(service):
    user = _make_user(service, email="api-user@example.com", username="api-user", display_name="API User")
    payload = service.api_identity(user_id=user["id"])

    assert payload["success"] is True
    assert payload["error"] is None
    assert payload["data"]["user"]["id"] == user["id"]
