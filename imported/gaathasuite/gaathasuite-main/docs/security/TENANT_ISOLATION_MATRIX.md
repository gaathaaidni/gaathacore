# Tenant Isolation Matrix

## Scope

This document captures the current tenant-isolation status for the active FastAPI runtime. It is intentionally conservative and reflects the evidence available in the current codebase.

## Current status

Status: YELLOW

Certain tenant-scoping patterns exist in the active application, especially in dashboard and auth flows, but full route-by-route evidence is not complete.

## Core expectations

For each protected route, the application should enforce:

- authenticated user required
- organization context derived from the current user
- resource belongs to the same organization
- object-level authorization enforced
- cross-organization reads denied
- cross-organization mutations denied
- superadmin access limited to intentional, documented exceptions

## Example matrix

| Route family | Auth required | Org scope required | Current evidence | Status |
| --- | --- | --- | --- | --- |
| `/auth/*` | Yes | Yes | User and organization creation paths exist | YELLOW |
| `/api/dashboard-stats` | Yes | Yes | Uses `current_user.organization_id` and filters counts by org | GREEN (limited) |
| `/api/v2/crm/*` | Yes | Yes | CRM routes exist but full tenant negative tests are incomplete | YELLOW |
| `/api/v2/inventory/*` | Yes | Yes | Inventory routes exist, but full cross-org integrity tests are incomplete | YELLOW |
| `/api/v2/books/*` | Yes | Yes | Invoice and accounting routes exist, but broader accounting security not yet fully validated | YELLOW |
| `/api/v2/expenses/*` | Yes | Yes | Expense routes exist, but approval and tenant enforcement need rigor | YELLOW |
| `/api/v1/download/` | Yes | Yes | Token is scoped to org and user in the smoke test | GREEN (limited) |
| `/legal/*` | Yes for some endpoints | Yes | Acceptance flows exist and versioning logic is present | YELLOW |

## Remaining requirement

Route-by-route negative tests must be added to prove that organization A cannot read, write, update, delete, or export organization B records.
