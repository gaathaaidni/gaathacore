# Active FastAPI Route Inventory

This inventory is limited to routes actually included by the active FastAPI application in `backend/app/main.py` and the routers it mounts. Legacy Flask routes are intentionally excluded because they are not part of the live FastAPI runtime.

## Scope and method

The authoritative runtime registers the following routers from `backend/app/main.py`:

- `app.tasks.notifications.router`
- `app.preferences.router`
- `app.tasks.auth.router`
- `app.routes.auth.router`
- `app.routes.approvals.router`
- `app.tasks.import_export.router`
- `blueprints.ai_assistant.routes.ai_router`
- `app.utils.downloads.router`
- `app.schemas.routes.router`
- `app.schemas.vendor_invoices.router`
- `app.schemas.vendor_management.router`
- `app.routes.hr.router`
- `app.routes.departments.router`
- `app.routes.legal.router`
- `blueprints.crm.routes_refactored.router`
- `blueprints.inventory.routes.router`
- `blueprints.books.routes_refactored.router`
- `blueprints.expenses.routes_refactored.router`
- `app.routes.transactions.router`

## Inventory

| METHOD | PATH | ROUTER | RESOURCE | TENANT OWNED | ROLE | PARENT | OWNERSHIP MECHANISM | TEST REQUIRED |
|---|---|---|---|---|---|---|---|---|
| GET | /health | app.main | health | N/A | public | N/A | none | N/A |
| GET | /_health | app.main | health | N/A | public | N/A | none | N/A |
| GET | /ready | app.main | readiness | N/A | public | N/A | none | N/A |
| GET | /api/dashboard-stats | app.main | dashboard | tenant-scoped | authenticated | user/org | `current_user.organization_id` | same-org only |
| POST | /auth/token | app.routes.auth | auth token | N/A | public | N/A | user credentials | login behavior |
| POST | /auth/login | app.routes.auth | auth login | N/A | public | N/A | user credentials | login behavior |
| POST | /auth/refresh | app.routes.auth | auth refresh | N/A | authenticated | user | token payload | refresh behavior |
| GET | /auth/users/me | app.routes.auth | user profile | tenant-scoped | authenticated | user | `current_user` | same-user only |
| PUT | /auth/users/me | app.routes.auth | user profile | tenant-scoped | authenticated | user | `current_user` | same-user update |
| GET | /auth/users | app.routes.auth | users | tenant-scoped | orgadmin/superadmin | org | `organization_id` filter | list isolation |
| POST | /auth/users | app.routes.auth | user creation | tenant-scoped | orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| PUT | /auth/users/{user_id} | app.routes.auth | user update | tenant-scoped | orgadmin/superadmin | org | org and role checks | update isolation |
| DELETE | /auth/users/{user_id} | app.routes.auth | user delete | tenant-scoped | orgadmin/superadmin | org | org check | delete isolation |
| POST | /auth/register | app.routes.auth | organization + user | tenant-scoped | public | org | new org + user record | registration |
| POST | /auth/password-reset-request | app.tasks.auth | password reset | tenant-scoped | public | user | user email lookup | N/A |
| POST | /auth/password-reset-confirm | app.tasks.auth | password reset confirm | tenant-scoped | public | user | token validation | N/A |
| GET | /notifications/ | app.tasks.notifications | notifications | tenant-scoped | authenticated | user/org | user/org association | list isolation |
| POST | /notifications/{notification_id}/read | app.tasks.notifications | notification | tenant-scoped | authenticated | user/org | current user scope | same-user only |
| GET | /settings/notifications/ | app.preferences | notification preferences | tenant-scoped | authenticated | user/org | `current_user.organization_id` | same-org only |
| POST | /settings/notifications/ | app.preferences | notification preferences | tenant-scoped | authenticated | user/org | `current_user.organization_id` | same-org only |
| GET | /download/ | app.utils.downloads | export download | tenant-scoped | authenticated | user/org | token/user/org match | export scoping |
| POST | /import/{resource_type} | app.tasks.import_export | import | tenant-scoped | authenticated/admin | org | org context | import isolation |
| POST | /import/export/{resource_type} | app.tasks.import_export | export | tenant-scoped | authenticated/admin | org | org context | export isolation |
| POST | /import/export/custom | app.tasks.import_export | custom export | tenant-scoped | authenticated/admin | org | org context | export isolation |
| GET | /legal/documents | app.routes.legal | legal docs | tenant-scoped | public/authenticated | org | document catalog | N/A |
| GET | /legal/documents/{slug} | app.routes.legal | legal doc | tenant-scoped | public/authenticated | org | document lookup | N/A |
| POST | /legal/acceptances | app.routes.legal | legal acceptance | tenant-scoped | authenticated | user/org | current user and org | same-user only |
| GET | /legal/acceptances/me | app.routes.legal | legal acceptance history | tenant-scoped | authenticated | user/org | current user scope | same-user only |
| GET | /api/v2/hr/employees | app.routes.hr | employees | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` filter | list isolation |
| GET | /api/v2/hr/employees/{employee_id} | app.routes.hr | employee | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` filter | get-id isolation |
| POST | /api/v2/hr/employees | app.routes.hr | employee | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` assignment | create isolation |
| PUT | /api/v2/hr/employees/{employee_id} | app.routes.hr | employee | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` check | update isolation |
| DELETE | /api/v2/hr/employees/{employee_id} | app.routes.hr | employee | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` check | delete isolation |
| GET | /api/v2/hr/payslips | app.routes.hr | payslip | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` filter | list isolation |
| POST | /api/v2/hr/payslips | app.routes.hr | payslip | tenant-owned | orgadmin/manager/superadmin | org | org scope | create isolation |
| POST | /api/v2/hr/payslips/{payslip_id}/process | app.routes.hr | payslip | tenant-owned | orgadmin/manager/superadmin | org | org scope | update isolation |
| POST | /api/v2/hr/payslips/calculate | app.routes.hr | payroll calculation | tenant-owned | orgadmin/manager/superadmin | org | org scope | calculate isolation |
| GET | /api/v2/hr/payroll/summary | app.routes.hr | payroll summary | tenant-owned | orgadmin/manager/superadmin | org | org scope | summary isolation |
| GET | /api/v2/hr/reviews | app.routes.hr | performance review | tenant-owned | orgadmin/manager/superadmin | org | `organization_id` filter | list isolation |
| POST | /api/v2/hr/reviews | app.routes.hr | performance review | tenant-owned | orgadmin/manager/superadmin | org | org scope | create isolation |
| PUT | /api/v2/hr/reviews/{review_id} | app.routes.hr | performance review | tenant-owned | orgadmin/manager/superadmin | org | org scope | update isolation |
| GET | /api/v2/hr/attendance | app.routes.hr | attendance | tenant-owned | orgadmin/manager/superadmin | org | org scope | list isolation |
| POST | /api/v2/hr/attendance | app.routes.hr | attendance | tenant-owned | orgadmin/manager/superadmin | org | org scope | create isolation |
| POST | /api/v2/hr/attendance/clock-in | app.routes.hr | attendance | tenant-owned | orgadmin/manager/superadmin | org | org scope | create isolation |
| POST | /api/v2/hr/attendance/clock-out | app.routes.hr | attendance | tenant-owned | orgadmin/manager/superadmin | org | org scope | create isolation |
| GET | /api/v2/hr/attendance/today | app.routes.hr | attendance | tenant-owned | orgadmin/manager/superadmin | org | org scope | list isolation |
| GET | /departments | app.routes.departments | departments | tenant-owned | orgadmin/superadmin | org | `organization_id` filter | list isolation |
| POST | /departments | app.routes.departments | department | tenant-owned | orgadmin/superadmin | org | `organization_id` assignment | create isolation |
| PUT | /departments/{dept_id} | app.routes.departments | department | tenant-owned | orgadmin/superadmin | org | `organization_id` check | update isolation |
| DELETE | /departments/{dept_id} | app.routes.departments | department | tenant-owned | orgadmin/superadmin | org | `organization_id` check | delete isolation |
| GET | /api/v2/crm/leads | blueprints.crm.routes_refactored | leads | tenant-owned | authenticated role set | org | `Lead.organization_id` | list isolation |
| POST | /api/v2/crm/leads | blueprints.crm.routes_refactored | lead | tenant-owned | lead/manager/orgadmin/superadmin | org | `get_org_db_session` | create isolation |
| PATCH | /api/v2/crm/leads/{lead_id} | blueprints.crm.routes_refactored | lead | tenant-owned | lead/manager/orgadmin/superadmin | org | `Lead.organization_id` | update isolation |
| GET | /api/v2/crm/opportunities | blueprints.crm.routes_refactored | opportunities | tenant-owned | authenticated role set | org | `Opportunity.organization_id` | list isolation |
| POST | /api/v2/crm/opportunities | blueprints.crm.routes_refactored | opportunity | tenant-owned | lead/manager/orgadmin/superadmin | org | `Customer.organization_id` + org scope | create isolation |
| PATCH | /api/v2/crm/opportunities/{opportunity_id} | blueprints.crm.routes_refactored | opportunity | tenant-owned | lead/manager/orgadmin/superadmin | org | `Opportunity.organization_id` | update isolation |
| GET | /api/v2/crm/customers | blueprints.crm.routes_refactored | customers | tenant-owned | authenticated role set | org | `Customer.organization_id` | list isolation |
| POST | /api/v2/crm/customers | blueprints.crm.routes_refactored | customer | tenant-owned | manager/lead/orgadmin/superadmin | org | `organization_id` from auth | create isolation |
| GET | /api/v2/crm/customers/{customer_id} | blueprints.crm.routes_refactored | customer | tenant-owned | authenticated role set | org | `Customer.organization_id` | get-id isolation |
| POST | /api/v2/crm/convert-lead/{lead_id} | blueprints.crm.routes_refactored | conversion | tenant-owned | manager/lead/orgadmin/superadmin | org | lead org + auth org | parent-child isolation |
| GET | /api/v2/inventory/warehouses | blueprints.inventory.routes | warehouses | tenant-owned | authenticated role set | org | `Warehouse.organization_id` | list isolation |
| POST | /api/v2/inventory/warehouses | blueprints.inventory.routes | warehouse | tenant-owned | manager/lead/orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| GET | /api/v2/inventory/warehouses/{warehouse_id} | blueprints.inventory.routes | warehouse | tenant-owned | authenticated role set | org | `Warehouse.organization_id` | get-id isolation |
| GET | /api/v2/inventory/items | blueprints.inventory.routes | items | tenant-owned | authenticated role set | org | `Item.organization_id` | list isolation |
| POST | /api/v2/inventory/items | blueprints.inventory.routes | item | tenant-owned | manager/lead/orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| GET | /api/v2/inventory/items/{item_id} | blueprints.inventory.routes | item | tenant-owned | authenticated role set | org | `Item.organization_id` | get-id isolation |
| PATCH | /api/v2/inventory/items/{item_id} | blueprints.inventory.routes | item | tenant-owned | manager/lead/orgadmin/superadmin | org | `Item.organization_id` | update isolation |
| DELETE | /api/v2/inventory/items/{item_id} | blueprints.inventory.routes | item | tenant-owned | manager/lead/orgadmin/superadmin | org | `Item.organization_id` | delete isolation |
| GET | /api/v2/inventory/stock-records | blueprints.inventory.routes | stock records | tenant-owned | authenticated role set | org | `StockRecord.organization_id` | list isolation |
| POST | /api/v2/inventory/stock-records | blueprints.inventory.routes | stock record | tenant-owned | manager/lead/orgadmin/superadmin | org | `StockRecord.organization_id` | create isolation |
| GET | /api/v2/inventory/stock-records/{stock_record_id} | blueprints.inventory.routes | stock record | tenant-owned | authenticated role set | org | `StockRecord.organization_id` | get-id isolation |
| POST | /api/v2/inventory/adjust | blueprints.inventory.routes | stock adjustment | tenant-owned | manager/lead/orgadmin/superadmin | item/warehouse | parent item/warehouse org match | parent ownership |
| GET | /api/v2/inventory/items/{item_id}/transactions | blueprints.inventory.routes | stock transactions | tenant-owned | authenticated role set | item/org | `StockTransaction.organization_id` | child ownership |
| GET | /api/v2/books/accounts | blueprints.books.routes_refactored | accounts | tenant-owned | auditor/manager/lead/orgadmin/superadmin | org | `Account.organization_id` | list isolation |
| POST | /api/v2/books/accounts | blueprints.books.routes_refactored | account | tenant-owned | manager/lead/orgadmin/superadmin | org | auth org | create isolation |
| GET | /api/v2/books/entities | blueprints.books.routes_refactored | entities | tenant-owned | auditor/manager/lead/orgadmin/superadmin | org | `Entity.organization_id` | list isolation |
| POST | /api/v2/books/entities | blueprints.books.routes_refactored | entity | tenant-owned | manager/lead/orgadmin/superadmin | org | auth org | create isolation |
| GET | /api/v2/books/invoices | blueprints.books.routes_refactored | invoices | tenant-owned | auditor/manager/lead/orgadmin/superadmin | org | `Invoice.organization_id` | list isolation |
| POST | /api/v2/books/invoices | blueprints.books.routes_refactored | invoice | tenant-owned | manager/lead/orgadmin/superadmin | org | customer org + auth org | create isolation |
| GET | /api/v2/books/invoices/{invoice_id} | blueprints.books.routes_refactored | invoice | tenant-owned | auditor/manager/lead/orgadmin/superadmin | org | `Invoice.organization_id` | get-id isolation |
| POST | /api/v2/books/invoices/{invoice_id}/pay | blueprints.books.routes_refactored | invoice payment | tenant-owned | manager/lead/orgadmin/superadmin | invoice/org | invoice org + auth org | financial isolation |
| GET | /api/v2/expenses/vendors | blueprints.expenses.routes_refactored | vendors | tenant-owned | authenticated role set | org | `Vendor.org_id` | list isolation |
| POST | /api/v2/expenses/vendors | blueprints.expenses.routes_refactored | vendor | tenant-owned | manager/lead/orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| GET | /api/v2/expenses/ | blueprints.expenses.routes_refactored | expenses | tenant-owned | authenticated role set | org | `Expense.org_id` | list isolation |
| POST | /api/v2/expenses/ | blueprints.expenses.routes_refactored | expense | tenant-owned | manager/lead/orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| GET | /api/v2/expenses/{expense_id} | blueprints.expenses.routes_refactored | expense | tenant-owned | authenticated role set | org | `Expense.org_id` | get-id isolation |
| PUT | /api/v2/expenses/{expense_id} | blueprints.expenses.routes_refactored | expense | tenant-owned | manager/lead/orgadmin/superadmin | org | `Expense.org_id` | update isolation |
| DELETE | /api/v2/expenses/{expense_id} | blueprints.expenses.routes_refactored | expense | tenant-owned | manager/lead/orgadmin/superadmin | org | `Expense.org_id` | delete isolation |
| POST | /api/v2/transactions/quotations | app.routes.transactions | quotation | tenant-owned | lead/manager/orgadmin/superadmin | org/customer | `Customer.organization_id` + `org_id` | create isolation |
| PATCH | /api/v2/transactions/quotations/{quotation_id} | app.routes.transactions | quotation | tenant-owned | lead/manager/orgadmin/superadmin | org | `Quotation.organization_id` | update isolation |
| POST | /api/v2/transactions/quotations/{quotation_id}/convert | app.routes.transactions | quotation conversion | tenant-owned | lead/manager/orgadmin/superadmin | org/customer | parent quotation + customer check | parent-child isolation |
| PATCH | /api/v2/transactions/sales-orders/{order_id} | app.routes.transactions | sales order | tenant-owned | lead/manager/orgadmin/superadmin | org | `SalesOrder.organization_id` | update isolation |
| POST | /api/v2/transactions/sales-orders/{order_id}/invoice | app.routes.transactions | sales order invoice | tenant-owned | lead/manager/orgadmin/superadmin | org/customer | order org + auth org | parent-child isolation |
| POST | /api/v2/transactions/sales-orders/{order_id}/fulfill | app.routes.transactions | fulfillment | tenant-owned | lead/manager/orgadmin/superadmin | org/warehouse | warehouse org + order org | parent-child isolation |
| POST | /api/v2/transactions/purchase-receipts | app.routes.transactions | purchase receipt | tenant-owned | lead/manager/orgadmin/superadmin | org/warehouse | warehouse + purchase order org | parent-child isolation |
| POST | /api/v2/transactions/vendor-bills | app.routes.transactions | vendor bill | tenant-owned | lead/manager/orgadmin/superadmin | org/vendor | vendor org + auth org | create isolation |
| POST | /api/v2/transactions/vendor-bills/{bill_id}/pay | app.routes.transactions | vendor bill payment | tenant-owned | lead/manager/orgadmin/superadmin | bill/org | bill org + auth org | financial isolation |
| GET | /approvals/requests | app.routes.approvals | approval requests | tenant-owned | manager/orgadmin/superadmin | org | `ApprovalRequest.org_id` | list isolation |
| POST | /approvals/requests | app.routes.approvals | approval request | tenant-owned | manager/orgadmin/superadmin | org | `get_current_org_id` | create isolation |
| POST | /approvals/requests/{request_id}/approve | app.routes.approvals | approval approval | tenant-owned | manager/orgadmin/superadmin | org | `ApprovalRequest.org_id` | parent-child isolation |
| POST | /approvals/requests/{request_id}/reject | app.routes.approvals | approval rejection | tenant-owned | manager/orgadmin/superadmin | org | `ApprovalRequest.org_id` | parent-child isolation |
| GET | /api/v2/settings/ | app.schemas.routes | org settings | tenant-owned | orgadmin/superadmin | org | `current_user.organization_id` | same-org only |
| PATCH | /api/v2/settings/ | app.schemas.routes | org settings | tenant-owned | orgadmin/superadmin | org | `current_user.organization_id` | same-org only |
| GET | /api/v2/vendor-invoices/ | app.schemas.vendor_invoices | vendor invoice captures | tenant-owned | orgadmin/superadmin | org | `current_user.organization_id` | list isolation |
| POST | /api/v2/vendor-invoices/ | app.schemas.vendor_invoices | vendor invoice capture | tenant-owned | orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| POST | /api/v2/vendor-invoices/{invoice_id}/approve | app.schemas.vendor_invoices | vendor invoice approval | tenant-owned | orgadmin/superadmin | org | `current_user.organization_id` | approval isolation |
| GET | /api/v2/vendors | app.schemas.vendors | vendors | tenant-owned | orgadmin/superadmin | org | `Organization` filter | list isolation |
| POST | /api/v2/vendors | app.schemas.vendors | vendor | tenant-owned | orgadmin/superadmin | org | `current_user.organization_id` | create isolation |
| PUT | /api/v2/vendors/{vendor_id} | app.schemas.vendors | vendor | tenant-owned | orgadmin/superadmin | org | vendor org check | update isolation |
| GET | /api/v2/purchase-orders | app.schemas.vendors | purchase orders | tenant-owned | orgadmin/superadmin | org | org scope | list isolation |
| POST | /api/v2/purchase-orders | app.schemas.vendors | purchase order | tenant-owned | orgadmin/superadmin | org | org scope | create isolation |
| PUT | /api/v2/purchase-orders/{po_id}/status | app.schemas.vendors | purchase order | tenant-owned | orgadmin/superadmin | org | org scope | update isolation |
| GET | /api/v2/vendors/performance | app.schemas.vendors | vendor performance | tenant-owned | orgadmin/superadmin | org | org scope | list isolation |
| GET | /api/v2/dashboard/summary | blueprints.auth.routes | dashboard summary | tenant-owned | authenticated | org | `current_user.organization_id` | same-org only |
| POST | /ai-assistant/… | blueprints.ai_assistant.routes | AI assistant | tenant-owned | authenticated | org | org ID / user scope | same-org only |

## Notes

- This inventory is intentionally limited to live FastAPI routes actually mounted from `backend/app/main.py`.
- Legacy Flask blueprints under `backend/blueprints/*` are not part of the active public API unless they are explicitly mounted in FastAPI.
- Several endpoints appear to be intentionally global or public (for example `health`, login, registration, legal documents). Those are documented as exceptions rather than forcing tenant-ownership tests that do not apply.
- The matrix is still intentionally focused on evidence required for the Phase 1 closure: tenant isolation, RBAC, and runtime boundary.
