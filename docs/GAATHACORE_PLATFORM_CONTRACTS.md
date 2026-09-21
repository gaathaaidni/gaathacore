# GaathaCore Platform Contracts

**Status:** additive Phase 3 baseline

These contracts define the shared boundary without merging product databases or changing existing product response formats. Existing services may adopt them through adapters. A product response must not be changed solely to match these contracts until its clients and compatibility requirements are verified.

## Canonical model

```text
User -> Organization -> Project -> Module -> Resource
```

Organization is the tenant boundary. Project is optional: organization-owned resources may omit `project_id` when a product genuinely has no project-level concept. A module is available only when organization module access is enabled and the user has the matching permission.

Canonical module identifiers are `business_suite`, `pos`, `sentira`, and `postpilot`.

## Roles and permissions

| Existing concept | Canonical role | Baseline permissions |
|---|---|---|
| Suite `superadmin` | `platform_admin` | `organization.read`, `organization.manage`, `project.read`, `project.manage`, `users.read`, `users.manage`, `billing.read`, `billing.manage`, `usage.read`, and all module access |
| Suite `orgadmin`, Sentira owner/admin roles | `organization_owner` or `organization_admin` | Organization and user administration, project administration, enabled module access |
| Suite `manager`, POS manager/admin | `manager` | Operational permissions granted by product adapter; no platform administration by default |
| Suite `lead`, POS staff with elevated permissions | `staff` | Explicit product permissions only |
| Sentira read/report roles and POS read-only users | `viewer` | Read permissions explicitly granted by adapter |
| Legacy roles without a verified equivalent | `unmapped` | No access until reviewed |

The mapping is a migration aid, not a production rename. `platform_admin` is a protected platform role and must be assigned through an approved administrative workflow. The named administrative and ownership identities are documentation only; no name is hardcoded into authorization.

## Module access

```text
organization module status = enabled/trial
AND user permission = <module>.access
AND project scope is valid when required
=> access granted
```

`postpilot` remains disabled for shared exposure until it has authenticated requests, organization/project ownership on every mutable resource, isolated social credentials, durable job ownership, and negative tenant tests.

## Request and API behavior

Adapters should accept or create `X-Request-ID`, propagate it to downstream calls, and include it in `meta` without putting credentials or tokens there. The standard envelope is defined in `contracts/api-envelope.v1.schema.json`.

Use these status semantics: `401` missing or invalid authentication, `403` authenticated but not permitted, `404` inaccessible resource where existence must not be disclosed, `409` state conflict, `422` validation failure, `429` rate limit, and `500` non-sensitive internal failure. Existing products retain their current routes until compatibility adapters are verified.

## Audit and usage

`contracts/audit-event.v1.schema.json` defines an append-only audit event. Audit metadata must exclude passwords, access tokens, refresh tokens, provider credentials, camera credentials, and raw social payload secrets.

`contracts/usage-event.v1.schema.json` is the billable-event contract. Usage is attributable to organization, optional project, module, feature, source service, user, quantity, unit, timestamp, and idempotency key. Billing may consume validated usage events later; no event authorizes a charge by itself.

## Authentication adapters

- Suite keeps JWT/password, refresh-cookie, and organization context until a federation adapter is proven.
- POS keeps Flask-Login sessions and restaurant scoping until a session adapter is verified.
- Sentira keeps JWT/Passport, organization RBAC, and refresh sessions.
- PostPilot must remain internal or protected behind an authenticated gateway; its current routes are not a tenant boundary.

Passwords are never copied between systems. Existing sessions are not invalidated by this contract layer.

## Database ownership

Potential future platform-owned records are users, organizations, memberships, projects, roles, permissions, module access, audit events, and usage events. Product business records remain product-owned. Any synchronization requires stable external IDs, idempotent outbox/inbox processing, reconciliation, backups, and a tested rollback checkpoint.