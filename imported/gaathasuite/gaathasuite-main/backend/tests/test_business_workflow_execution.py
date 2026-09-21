import os

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL must point to an isolated PostgreSQL database",
)


@pytest.fixture
def release_client():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        yield client


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


def test_core_business_workflow_round_trip(api_client):
    register(api_client, "workflow_admin", "workflow-admin@example.com", "Workflow Tenant")
    token = login(api_client, "workflow_admin")
    headers = {"Authorization": f"Bearer {token}"}

    customer = api_client.post(
        "/api/v2/crm/customers",
        headers=headers,
        json={
            "name": "Acme Corp",
            "email": "sales@acme.example",
            "phone": "+1-555-0100",
            "company": "Acme Corp",
        },
    )
    assert customer.status_code == 201, customer.text
    customer_id = customer.json()["id"]

    warehouse = api_client.post(
        "/api/v2/inventory/warehouses",
        headers=headers,
        json={"name": "Main Warehouse", "location": "HQ"},
    )
    assert warehouse.status_code == 201, warehouse.text
    warehouse_id = warehouse.json()["id"]

    item = api_client.post(
        "/api/v2/inventory/items",
        headers=headers,
        json={
            "sku": "SKU-1001",
            "name": "Widget",
            "description": "Core business widget",
            "category": "Hardware",
            "sale_price": 150.0,
            "purchase_cost": 90.0,
            "min_stock_level": 5.0,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["id"]

    stock = api_client.post(
        "/api/v2/inventory/stock-records",
        headers=headers,
        json={"item_id": item_id, "warehouse_id": warehouse_id, "quantity": 12},
    )
    assert stock.status_code == 201, stock.text

    adjustment = api_client.post(
        "/api/v2/inventory/adjust",
        headers=headers,
        json={
            "item_id": item_id,
            "warehouse_id": warehouse_id,
            "adjustment_qty": 3,
            "note": "Initial saleable stock",
        },
    )
    assert adjustment.status_code == 200, adjustment.text
    assert adjustment.json()["quantity"] == 15

    negative_adjustment = api_client.post(
        "/api/v2/inventory/adjust",
        headers=headers,
        json={
            "item_id": item_id,
            "warehouse_id": warehouse_id,
            "adjustment_qty": -16,
            "note": "Should be rejected",
        },
    )
    assert negative_adjustment.status_code == 409, negative_adjustment.text

    invoice = api_client.post(
        "/api/v2/books/invoices",
        headers=headers,
        json={
            "number": "INV-1001",
            "customer_id": customer_id,
            "date": "2024-05-01",
            "due_date": "2024-05-15",
            "currency": "USD",
            "status": "draft",
            "notes": "Initial invoice for the workflow test",
            "lines": [
                {"description": "Widget sale", "qty": 2, "unit_price": 150.0},
                {"description": "Service support", "qty": 1, "unit_price": 75.0},
            ],
        },
    )
    assert invoice.status_code == 201, invoice.text
    invoice_data = invoice.json()
    assert invoice_data["total_amount"] == 375.0
    assert invoice_data["customer_id"] == customer_id

    partial = api_client.post(
        f"/api/v2/books/invoices/{invoice_data['id']}/pay",
        headers=headers,
        json={"amount": "100.00", "reference": "PARTIAL-1"},
    )
    assert partial.status_code == 200, partial.text
    assert partial.json()["status"] == "partially_paid"
    assert partial.json()["paid_amount"] == 100.0

    paid = api_client.post(
        f"/api/v2/books/invoices/{invoice_data['id']}/pay",
        headers=headers,
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "paid"
    assert paid.json()["outstanding_amount"] == 0.0


def test_expense_approval_workflow_round_trip(api_client):
    register(api_client, "expense_admin", "expense-admin@example.com", "Expense Tenant")
    token = login(api_client, "expense_admin")
    headers = {"Authorization": f"Bearer {token}"}

    vendor = api_client.post(
        "/api/v2/expenses/vendors",
        headers=headers,
        json={"name": "Cloud Telecom", "email": "billing@cloud-telecom.example", "category": "Utilities"},
    )
    assert vendor.status_code in {200, 201}, vendor.text

    expense = api_client.post(
        "/api/v2/expenses/",
        headers=headers,
        json={
            "amount": "245.75",
            "category": "Utilities",
            "description": "Monthly telecom expense",
            "expense_date": "2024-05-05",
            "vendor_id": vendor.json()["id"],
            "currency": "USD",
            "receipt_url": "https://example.com/receipt.pdf",
        },
    )
    assert expense.status_code == 201, expense.text
    expense_id = expense.json()["id"]

    approval = api_client.post(
        "/approvals/requests",
        headers=headers,
        json={
            "document_type": "expense",
            "document_id": expense_id,
            "amount": "245.75",
            "reason": "Approval required before payment",
            "requested_by_user_id": 1,
        },
    )
    assert approval.status_code == 201, approval.text
    approval_id = approval.json()["id"]

    approved = api_client.post(
        f"/approvals/requests/{approval_id}/approve",
        headers=headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    expense_after = api_client.get(f"/api/v2/expenses/{expense_id}", headers=headers)
    assert expense_after.status_code == 200, expense_after.text
    assert expense_after.json()["status"] == "approved"


def test_accounting_post_rejects_unbalanced_journal(api_client):
    register(api_client, "accounting_admin", "accounting-admin@example.com", "Accounting Tenant")
    token = login(api_client, "accounting_admin")
    headers = {"Authorization": f"Bearer {token}"}

    cash = api_client.post(
        "/api/v2/books/accounts",
        headers=headers,
        json={"name": "Cash", "type": "Asset", "code": "1000"},
    )
    assert cash.status_code == 201, cash.text

    receivables = api_client.post(
        "/api/v2/books/accounts",
        headers=headers,
        json={"name": "Accounts Receivable", "type": "Asset", "code": "1100"},
    )
    assert receivables.status_code == 201, receivables.text

    from app.db import AsyncSessionLocal
    from app.services.accounting import post_journal_entry, JournalValidationError

    async def _run_validation():
        async with AsyncSessionLocal() as session:
            with pytest.raises(JournalValidationError):
                await post_journal_entry(
                    db=session,
                    org_id=1,
                    description="Unbalanced test entry",
                    lines=[
                        {"account_id": cash.json()["id"], "debit": 100.00},
                        {"account_id": receivables.json()["id"], "credit": 50.00},
                    ],
                )

    import asyncio
    asyncio.run(_run_validation())


def test_posted_journal_entries_and_lines_are_immutable(api_client):
    register(api_client, "immutability_admin", "immutability-admin@example.com", "Immutability Tenant")
    token = login(api_client, "immutability_admin")
    headers = {"Authorization": f"Bearer {token}"}

    account_ids = []
    for code in ("1000", "1100"):
        response = api_client.post(
            "/api/v2/books/accounts",
            headers=headers,
            json={"name": f"Account {code}", "type": "Asset", "code": code},
        )
        assert response.status_code == 201, response.text
        account_ids.append(response.json()["id"])

    from app.db import AsyncSessionLocal
    from app.models.books import JournalEntry, JournalLine
    from app.services.accounting import post_journal_entry

    import asyncio

    async def _exercise_immutability():
        async with AsyncSessionLocal() as session:
            entry = await post_journal_entry(
                db=session,
                org_id=1,
                description="Posted immutable entry",
                lines=[
                    {"account_id": account_ids[0], "debit": 100.00},
                    {"account_id": account_ids[1], "credit": 100.00},
                ],
            )
            await session.commit()
            entry_id = entry.id

        async with AsyncSessionLocal() as session:
            posted = await session.get(JournalEntry, entry_id)
            posted.description = "Tampered description"
            with pytest.raises(ValueError, match="immutable"):
                await session.commit()
            await session.rollback()

            posted = await session.get(JournalEntry, entry_id)
            with pytest.raises(ValueError, match="immutable"):
                await session.delete(posted)
            await session.rollback()
            await session.close()

            async with AsyncSessionLocal() as line_session:
                lines = (await line_session.execute(select(JournalLine))).scalars().all()
                line = next(line for line in lines if line.entry_id == entry_id)
                line.debit = 99.0
                with pytest.raises(ValueError, match="immutable"):
                    await line_session.commit()
                await line_session.rollback()

                lines = (await line_session.execute(select(JournalLine))).scalars().all()
                line = next(line for line in lines if line.entry_id == entry_id)
                with pytest.raises(ValueError, match="immutable"):
                    await line_session.delete(line)
                await line_session.rollback()

                line_session.add(
                    JournalLine(
                        entry_id=entry_id,
                        account_id=account_ids[0],
                        organization_id=1,
                        debit=1.0,
                        credit=0.0,
                    )
                )
                with pytest.raises(ValueError, match="new lines"):
                    await line_session.commit()
                await line_session.rollback()

            async with AsyncSessionLocal() as verify_session:
                remaining = await verify_session.get(JournalEntry, entry_id)
                assert remaining.status == "posted"
                lines = (await verify_session.execute(select(JournalLine))).scalars().all()
                assert len([line for line in lines if line.entry_id == entry_id]) == 2

    asyncio.run(_exercise_immutability())


def test_vendor_bill_payment_is_scoped_idempotent_and_atomic(api_client, monkeypatch):
    register(api_client, "vendor_a_admin", "vendor-a@example.com", "Vendor Tenant A")
    register(api_client, "vendor_b_admin", "vendor-b@example.com", "Vendor Tenant B")
    headers_a = {"Authorization": f"Bearer {login(api_client, 'vendor_a_admin')}"}
    headers_b = {"Authorization": f"Bearer {login(api_client, 'vendor_b_admin')}"}

    vendor = api_client.post(
        "/api/v2/expenses/vendors",
        headers=headers_a,
        json={"name": "Tenant A Vendor", "email": "billing@a.example", "category": "Services"},
    )
    assert vendor.status_code == 201, vendor.text
    bill = api_client.post(
        "/api/v2/transactions/vendor-bills",
        headers=headers_a,
        json={
            "vendor_id": vendor.json()["id"],
            "bill_number": "BILL-A-1",
            "bill_date": "2026-09-13",
            "currency": "USD",
            "subtotal": "100.00",
            "tax": "0.00",
        },
    )
    assert bill.status_code == 201, bill.text
    bill_id = bill.json()["id"]

    cross_tenant = api_client.post(
        f"/api/v2/transactions/vendor-bills/{bill_id}/pay",
        headers=headers_b,
        json={"amount": "100.00", "reference": "CROSS-TENANT"},
    )
    assert cross_tenant.status_code == 404, cross_tenant.text

    first = api_client.post(
        f"/api/v2/transactions/vendor-bills/{bill_id}/pay",
        headers=headers_a,
        json={"amount": "100.00", "reference": "BILL-A-PAY-1"},
    )
    assert first.status_code == 200, first.text
    retry = api_client.post(
        f"/api/v2/transactions/vendor-bills/{bill_id}/pay",
        headers=headers_a,
        json={"amount": "100.00", "reference": "BILL-A-PAY-1"},
    )
    assert retry.status_code == 200, retry.text
    assert retry.json()["paid_amount"] == 100.0

    from app.routes import transactions
    from app.db import AsyncSessionLocal
    from app.models.transactions import VendorBill, VendorBillPayment

    async def fail_posting(*args, **kwargs):
        from app.services.accounting import JournalValidationError
        raise JournalValidationError("forced posting failure")

    monkeypatch.setattr(transactions, "post_journal_entry", fail_posting)

    second_bill = api_client.post(
        "/api/v2/transactions/vendor-bills",
        headers=headers_a,
        json={
            "vendor_id": vendor.json()["id"],
            "bill_number": "BILL-A-2",
            "bill_date": "2026-09-13",
            "currency": "USD",
            "subtotal": "50.00",
            "tax": "0.00",
        },
    )
    assert second_bill.status_code == 201, second_bill.text
    second_bill_id = second_bill.json()["id"]
    failed = api_client.post(
        f"/api/v2/transactions/vendor-bills/{second_bill_id}/pay",
        headers=headers_a,
        json={"amount": "50.00", "reference": "BILL-A-FAIL"},
    )
    assert failed.status_code == 422, failed.text

    import asyncio

    async def verify_rollback():
        async with AsyncSessionLocal() as session:
            bill_state = await session.get(VendorBill, second_bill_id)
            assert bill_state.paid_amount == 0
            payment_count = await session.scalar(
                select(func.count())
                .select_from(VendorBillPayment)
                .where(VendorBillPayment.vendor_bill_id == second_bill_id)
            )
            assert payment_count == 0

    asyncio.run(verify_rollback())


def test_invoice_payment_is_scoped_and_idempotent(api_client):
    org_a = register(api_client, "invoice_org_a", "invoice-a@example.com", "Invoice Org A")
    org_b = register(api_client, "invoice_org_b", "invoice-b@example.com", "Invoice Org B")
    token_a = login(api_client, "invoice_org_a")
    token_b = login(api_client, "invoice_org_b")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    customer = api_client.post(
        "/api/v2/crm/customers",
        headers=headers_a,
        json={
            "name": "Invoice Customer",
            "email": "customer@example.com",
            "phone": "+1-555-0001",
            "company": "Invoice Customer LLC",
        },
    )
    assert customer.status_code == 201, customer.text

    foreign_customer = api_client.post(
        "/api/v2/crm/customers",
        headers=headers_b,
        json={
            "name": "Tenant B Customer",
            "email": "customer-b@example.com",
            "phone": "+1-555-0002",
            "company": "Tenant B Customer LLC",
        },
    )
    assert foreign_customer.status_code == 201, foreign_customer.text

    cross_tenant_invoice = api_client.post(
        "/api/v2/books/invoices",
        headers=headers_a,
        json={
            "number": "INV-CROSS-TENANT",
            "customer_id": foreign_customer.json()["id"],
            "date": "2024-06-01",
            "currency": "USD",
            "status": "draft",
            "lines": [{"description": "Blocked", "qty": 1, "unit_price": 1}],
        },
    )
    assert cross_tenant_invoice.status_code == 404, cross_tenant_invoice.text

    for code in ("1000", "1100"):
        response = api_client.post(
            "/api/v2/books/accounts",
            headers=headers_a,
            json={"name": f"Account {code}", "type": "Asset", "code": code},
        )
        assert response.status_code == 201, response.text

    invoice = api_client.post(
        "/api/v2/books/invoices",
        headers=headers_a,
        json={
            "number": "INV-ORG-A-1",
            "customer_id": customer.json()["id"],
            "date": "2024-06-01",
            "due_date": "2024-06-15",
            "currency": "USD",
            "status": "draft",
            "notes": "Org A invoice",
            "lines": [
                {"description": "Widget", "qty": 2, "unit_price": 150.00},
            ],
        },
    )
    assert invoice.status_code == 201, invoice.text
    invoice_id = invoice.json()["id"]

    cross_org = api_client.post(
        f"/api/v2/books/invoices/{invoice_id}/pay",
        headers=headers_b,
        json={"amount": "300.00", "reference": "ORG-B-RETRY"},
    )
    assert cross_org.status_code in {403, 404}, cross_org.text

    first_payment = api_client.post(
        f"/api/v2/books/invoices/{invoice_id}/pay",
        headers=headers_a,
        json={"amount": "300.00", "reference": "ORG-A-RETRY"},
    )
    assert first_payment.status_code == 200, first_payment.text

    second_payment = api_client.post(
        f"/api/v2/books/invoices/{invoice_id}/pay",
        headers=headers_a,
        json={"amount": "300.00", "reference": "ORG-A-RETRY"},
    )
    assert second_payment.status_code == 200, second_payment.text
    assert second_payment.json()["paid_amount"] == 300.0

    from sqlalchemy import text
    from app.db import AsyncSessionLocal

    async def _count_payments():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM payment WHERE invoice_id = :invoice_id AND reference = :reference"),
                {"invoice_id": invoice_id, "reference": "ORG-A-RETRY"},
            )
            return int(result.scalar_one())

    import asyncio
    assert asyncio.run(_count_payments()) == 1


def test_crm_lead_to_won_opportunity_to_customer(api_client):
    register(api_client, "crm_admin", "crm-admin@example.com", "CRM Tenant")
    token = login(api_client, "crm_admin")
    headers = {"Authorization": f"Bearer {token}"}

    lead = api_client.post(
        "/api/v2/crm/leads",
        headers=headers,
        json={
            "name": "Jordan Smith",
            "contact_email": "jordan@example.com",
            "company": "Northwind Services",
            "source": "referral",
        },
    )
    assert lead.status_code == 201, lead.text
    lead_id = lead.json()["id"]

    qualified = api_client.patch(
        f"/api/v2/crm/leads/{lead_id}",
        headers=headers,
        json={"status": "qualified"},
    )
    assert qualified.status_code == 200, qualified.text
    assert qualified.json()["status"] == "qualified"

    converted = api_client.post(f"/api/v2/crm/convert-lead/{lead_id}", headers=headers)
    assert converted.status_code == 200, converted.text
    customer_id = converted.json()["customer_id"]

    opportunity = api_client.post(
        "/api/v2/crm/opportunities",
        headers=headers,
        json={
            "title": "Northwind implementation",
            "customer_id": customer_id,
            "value": 12000,
            "stage": "proposal",
        },
    )
    assert opportunity.status_code == 201, opportunity.text

    won = api_client.patch(
        f"/api/v2/crm/opportunities/{opportunity.json()['id']}",
        headers=headers,
        json={"stage": "won"},
    )
    assert won.status_code == 200, won.text
    assert won.json()["stage"] == "won"

    customer = api_client.get(f"/api/v2/crm/customers/{customer_id}", headers=headers)
    assert customer.status_code == 200, customer.text
    me = api_client.get("/auth/users/me", headers=headers)
    assert me.status_code == 200, me.text
    assert customer.json()["organization_id"] == me.json()["organization_id"]


def test_sales_and_purchase_transaction_flows(api_client):
    register(api_client, "transaction_admin", "transaction-admin@example.com", "Transaction Tenant")
    token = login(api_client, "transaction_admin")
    headers = {"Authorization": f"Bearer {token}"}

    customer = api_client.post(
        "/api/v2/crm/customers", headers=headers,
        json={"name": "Transaction Customer", "email": "customer@transaction.example", "company": "Transaction Co"},
    )
    warehouse = api_client.post(
        "/api/v2/inventory/warehouses", headers=headers,
        json={"name": "Transaction Warehouse", "location": "HQ"},
    )
    item = api_client.post(
        "/api/v2/inventory/items", headers=headers,
        json={"sku": "TX-100", "name": "Transaction Item", "sale_price": 25, "purchase_cost": 10},
    )
    assert customer.status_code == warehouse.status_code == item.status_code == 201
    customer_id, warehouse_id, item_id = customer.json()["id"], warehouse.json()["id"], item.json()["id"]
    stock = api_client.post(
        "/api/v2/inventory/stock-records", headers=headers,
        json={"item_id": item_id, "warehouse_id": warehouse_id, "quantity": 10},
    )
    assert stock.status_code == 201, stock.text

    quotation = api_client.post(
        "/api/v2/transactions/quotations", headers=headers,
        json={"customer_id": customer_id, "quotation_number": "Q-TX-1", "quotation_date": "2026-09-12", "lines": [{"item_id": item_id, "description": "Transaction Item", "quantity": "4", "unit_price": "25", "tax": "2"}]},
    )
    assert quotation.status_code == 201, quotation.text
    quotation_id = quotation.json()["id"]
    accepted = api_client.patch(f"/api/v2/transactions/quotations/{quotation_id}", headers=headers, json={"status": "accepted"})
    assert accepted.status_code == 200, accepted.text

    order = api_client.post(
        f"/api/v2/transactions/quotations/{quotation_id}/convert", headers=headers,
        json={"customer_id": customer_id, "order_number": "SO-TX-1", "order_date": "2026-09-12", "lines": [{"item_id": item_id, "description": "Transaction Item", "quantity": "4", "unit_price": "25", "tax": "2"}]},
    )
    assert order.status_code == 201, order.text
    order_id = order.json()["id"]
    confirmed = api_client.patch(f"/api/v2/transactions/sales-orders/{order_id}", headers=headers, json={"status": "confirmed"})
    assert confirmed.status_code == 200, confirmed.text
    fulfilled = api_client.post(f"/api/v2/transactions/sales-orders/{order_id}/fulfill", headers=headers, json={"warehouse_id": warehouse_id, "fulfillment_number": "FUL-TX-1"})
    assert fulfilled.status_code == 201, fulfilled.text
    stock_after_sale = api_client.get("/api/v2/inventory/stock-records", headers=headers)
    assert stock_after_sale.json()[0]["quantity"] == 6
    invoice = api_client.post(f"/api/v2/transactions/sales-orders/{order_id}/invoice?number=INV-TX-1", headers=headers)
    assert invoice.status_code == 201, invoice.text
    assert invoice.json()["total"] == 102.0

    vendor = api_client.post("/api/v2/vendors", headers=headers, json={"name": "Transaction Vendor", "email": "vendor@transaction.example"})
    assert vendor.status_code == 201, vendor.text
    po = api_client.post("/api/v2/purchase-orders", headers=headers, json={"vendor_id": vendor.json()["id"], "reference_number": "PO-TX-1", "total_amount": 30, "status": "ordered"})
    assert po.status_code == 201, po.text
    receipt = api_client.post("/api/v2/transactions/purchase-receipts", headers=headers, json={"purchase_order_id": po.json()["id"], "warehouse_id": warehouse_id, "receipt_number": "REC-TX-1", "lines": [{"item_id": item_id, "received_quantity": "7"}]})
    assert receipt.status_code == 201, receipt.text
    stock_after_receipt = api_client.get("/api/v2/inventory/stock-records", headers=headers)
    assert stock_after_receipt.json()[0]["quantity"] == 13
    bill = api_client.post("/api/v2/transactions/vendor-bills", headers=headers, json={"vendor_id": vendor.json()["id"], "purchase_order_id": po.json()["id"], "bill_number": "BILL-TX-1", "bill_date": "2026-09-12", "subtotal": "30", "tax": "3"})
    assert bill.status_code == 201, bill.text
    assert bill.json()["total"] == 33.0
    bill_partial = api_client.post(f"/api/v2/transactions/vendor-bills/{bill.json()['id']}/pay", headers=headers, json={"amount": "10", "reference": "VENDOR-PARTIAL-1"})
    assert bill_partial.status_code == 200, bill_partial.text
    assert bill_partial.json()["status"] == "partially_paid"
    assert bill_partial.json()["outstanding"] == 23.0
    bill_paid = api_client.post(f"/api/v2/transactions/vendor-bills/{bill.json()['id']}/pay", headers=headers, json={"amount": "23", "reference": "VENDOR-FINAL-1"})
    assert bill_paid.status_code == 200, bill_paid.text
    assert bill_paid.json()["status"] == "paid"
    assert bill_paid.json()["outstanding"] == 0.0


def test_release_health_readiness_headers_and_frontend_fallback(release_client, monkeypatch):
    from app import main as main_module

    class WorkingConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        async def execute(self, _query):
            return None

    monkeypatch.setattr(type(main_module.engine), "connect", lambda _engine: WorkingConnection())

    health = release_client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["content-type"].startswith("application/json")

    ready = release_client.get("/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "dependencies": {"database": "available"}}

    frontend = release_client.get("/dashboard")
    assert frontend.status_code == 200
    assert "<div id=\"root\"></div>" in frontend.text

    unknown_api = release_client.get("/api/does-not-exist")
    assert unknown_api.status_code == 404
    assert unknown_api.json()["error"]["code"] == "HTTP_404"

    for path in (
        "/.git/config",
        "/.env",
        "/.env.tmp",
        "/.aws/credentials.backup",
        "/terraform.tfstate.bak",
        "/docker-compose.yml.backup",
        "/backup.sql",
        "/requirements.txt",
        "/package.json",
        "/Dockerfile",
        "/.gitignore",
    ):
        response = release_client.get(path)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "HTTP_404"

    for header in (
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "content-security-policy",
        "permissions-policy",
    ):
        assert header in {name.lower() for name in frontend.headers}

    static_asset = release_client.get("/static/dist/icon.png")
    assert static_asset.status_code == 200


def test_release_readiness_returns_503_when_database_is_unavailable(release_client, monkeypatch):
    from app import main as main_module

    class UnavailableConnection:
        async def __aenter__(self):
            raise ConnectionError("database unavailable")

        async def __aexit__(self, *_):
            return False

    monkeypatch.setattr(type(main_module.engine), "connect", lambda _engine: UnavailableConnection())

    response = release_client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "dependencies": {"database": "unavailable"}}
