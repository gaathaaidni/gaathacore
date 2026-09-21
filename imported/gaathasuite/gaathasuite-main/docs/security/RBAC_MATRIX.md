# RBAC Matrix

## Current status

Status: YELLOW

The application contains role-based authorization patterns and some negative tests, but a complete canonical RBAC matrix across all protected actions is not yet fully proven.

## Expected roles

- `superadmin`
- `organization_admin`
- `manager`
- `user`
- possibly role-specific operational roles depending on the route family

## Expected policy

| Action | Role | Scope | Expected outcome |
| --- | --- | --- | --- |
| Create organization-level admin | superadmin | global | allowed |
| Create another organization user | org admin | same org only | denied |
| Assign superadmin role | org admin | local org only | denied |
| Manipulate another org resource | org admin | same org only | denied |
| Read own org data | user/manager/admin | same org | allowed |
| Read another org data | user/manager/admin | cross-org | denied |
| Modify same org resource | manager/admin | same org | allowed |
| Delete same org resource | admin | same org | allowed when policy permits |

## Evidence available

- Auth smoke tests validate org-admin rejection of superadmin assignment.
- Org-admin cross-tenant user creation is rejected.

## Remaining requirement

The matrix needs a full object-level authorization test set covering all sensitive modules: customers, inventory, invoices, payments, vendors, employees, accounting, exports, files, approvals, and audit logs.
