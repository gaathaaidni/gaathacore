import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL must point to an isolated PostgreSQL database",
)


def register(client, username, email, organization):
    response = client.post(
        "/auth/register",
        json={
            "organizationName": organization,
            "industry": "Professional services",
            "companySize": "SME",
            "username": username,
            "email": email,
            "password": "A-strong-test-password-123",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def login(client, username):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": "A-strong-test-password-123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_registration_login_and_tenant_scoped_dashboard(api_client):
    organization_a_user = register(
        api_client, "tenant_a_admin", "tenant-a@example.com", "Tenant A"
    )
    organization_b_user = register(
        api_client, "tenant_b_admin", "tenant-b@example.com", "Tenant B"
    )

    from sqlalchemy import text
    from app.db import AsyncSessionLocal

    async def add_customer(organization_id):
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    "INSERT INTO customers (organization_id, name, email, currency, is_active) "
                    "VALUES (:organization_id, :name, :email, :currency, :is_active)"
                ),
                {
                    "organization_id": organization_id,
                    "name": "Private customer",
                    "email": "private-customer@example.com",
                    "currency": "USD",
                    "is_active": True,
                },
            )
            await session.commit()

    import asyncio

    asyncio.run(add_customer(organization_a_user["organization_id"]))

    token_a = login(api_client, "tenant_a_admin")
    dashboard_a = api_client.get(
        "/api/dashboard-stats", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert dashboard_a.status_code == 200
    assert dashboard_a.json()["customers"] == 1

    token_b = login(api_client, "tenant_b_admin")
    dashboard_b = api_client.get(
        "/api/dashboard-stats", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert dashboard_b.status_code == 200
    assert dashboard_b.json()["customers"] == 0


def test_org_admin_cannot_assign_superadmin_role(api_client):
    register(api_client, "role_admin", "role-admin@example.com", "Role Tenant")
    token = login(api_client, "role_admin")

    response = api_client.post(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "escalated",
            "email": "escalated@example.com",
            "password": "A-strong-test-password-123",
            "role": "superadmin",
        },
    )
    assert response.status_code == 403


def test_org_admin_cannot_create_user_for_another_organization(api_client):
    org_a = register(api_client, "tenant_a_admin", "tenant-a@example.com", "Tenant A")
    org_b = register(api_client, "tenant_b_admin", "tenant-b@example.com", "Tenant B")
    token = login(api_client, "tenant_a_admin")

    response = api_client.post(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "cross_tenant_user",
            "email": "cross-tenant@example.com",
            "password": "A-strong-test-password-123",
            "role": "user",
            "organization_id": org_b["organization_id"],
        },
    )
    assert response.status_code == 403
    assert "organization" in response.json()["error"]["message"].lower()


def test_standard_user_cannot_access_admin_mutations(api_client):
    register(api_client, "rbac_admin", "rbac-admin@example.com", "RBAC Tenant")
    admin_token = login(api_client, "rbac_admin")
    created = api_client.post(
        "/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "rbac_member",
            "email": "rbac-member@example.com",
            "password": "A-strong-test-password-123",
            "role": "user",
        },
    )
    assert created.status_code == 200, created.text

    member_token = login(api_client, "rbac_member")
    member_headers = {"Authorization": f"Bearer {member_token}"}
    assert api_client.get("/auth/users", headers=member_headers).status_code == 403
    assert api_client.post(
        "/api/v2/books/accounts",
        headers=member_headers,
        json={"name": "Blocked", "type": "Asset", "code": "9999"},
    ).status_code == 403
    assert api_client.post(
        "/api/v2/expenses/vendors",
        headers=member_headers,
        json={"name": "Blocked Vendor", "email": "blocked@example.com", "category": "Other"},
    ).status_code == 403


def test_authentication_rejects_invalid_inactive_and_unauthorized_requests(api_client):
    invalid_login = api_client.post(
        "/auth/login",
        json={"username": "missing", "password": "wrong"},
    )
    assert invalid_login.status_code == 401

    register(api_client, "inactive_user", "inactive@example.com", "Inactive Tenant")
    from app.db import AsyncSessionLocal
    from sqlalchemy import text

    async def deactivate_user():
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE users SET is_active = FALSE WHERE username = :username"),
                {"username": "inactive_user"},
            )
            await session.commit()

    import asyncio

    asyncio.run(deactivate_user())
    inactive_login = api_client.post(
        "/auth/login",
        json={
            "username": "inactive_user",
            "password": "A-strong-test-password-123",
        },
    )
    assert inactive_login.status_code == 403

    unauthorized = api_client.get("/api/dashboard-stats")
    assert unauthorized.status_code == 401

    malformed = api_client.get(
        "/api/dashboard-stats",
        headers={"Authorization": "Bearer malformed.token"},
    )
    assert malformed.status_code == 401


def test_versioned_legal_documents_and_acceptance_are_auditable(api_client):
    register(api_client, "legal_user", "legal@example.com", "Legal Tenant")
    token = login(api_client, "legal_user")
    headers = {"Authorization": f"Bearer {token}"}

    documents = api_client.get("/legal/documents")
    assert documents.status_code == 200
    privacy = next(document for document in documents.json() if document["slug"] == "privacy")
    assert privacy["version"] == "1.0"

    accepted = api_client.post(
        "/legal/acceptances",
        headers=headers,
        json={"slug": "privacy", "version": "1.0"},
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["accepted_at"]

    history = api_client.get("/legal/acceptances/me", headers=headers)
    assert history.status_code == 200
    assert {item["slug"] for item in history.json()} == {"privacy"}


def test_export_download_token_is_scoped_to_org_and_user(api_client):
    org_a = register(api_client, "tenant_a_exporter", "tenant-a-export@example.com", "Tenant A")
    org_b = register(api_client, "tenant_b_exporter", "tenant-b-export@example.com", "Tenant B")

    from app.utils.signing import generate_token

    export_path = "/tmp/export_cross_tenant_test.csv"
    with open(export_path, "w", encoding="utf-8") as handle:
        handle.write("id,name\n1,Example\n")

    token_for_org_a = generate_token({
        "path": export_path,
        "user_id": 1,
        "org_id": org_a["organization_id"],
    })

    token_a = login(api_client, "tenant_a_exporter")
    same_org = api_client.get(
        "/api/v1/download/",
        headers={"Authorization": f"Bearer {token_a}"},
        params={"token": token_for_org_a},
    )
    assert same_org.status_code == 200

    token_b = login(api_client, "tenant_b_exporter")
    cross_org = api_client.get(
        "/api/v1/download/",
        headers={"Authorization": f"Bearer {token_b}"},
        params={"token": token_for_org_a},
    )
    assert cross_org.status_code == 403
