# GAATHACORE Phase 3 Report

**Phase:** 3 - GaathaCore Core Platform Layer  
**Date:** 2026-09-21  
**Workspace:** `/workspaces/gaathacore`  
**Status:** Additive contract foundation implemented; runtime federation and PostPilot exposure remain blocked

## Executive Summary

Phase 3 establishes the first safe GaathaCore platform layer without rewriting the four products, merging databases, changing production domains, invalidating sessions, touching the VPS, or enabling billing charges.

Implemented now:

- A versioned API envelope schema.
- A versioned request context and module-access schema.
- A versioned audit-event schema.
- A platform contract document covering identity, organization, project, module, RBAC, adapters, correlation, audit, usage, and database ownership.
- A Phase 2 handoff addendum.

Designed but not implemented:

- Canonical identity and organization database tables.
- Identity federation and product authentication adapters.
- Central module-access evaluation at runtime.
- Audit and usage producers/ledgers.
- Project-aware product resource mapping.

Blocked or unsafe to expose:

- PostPilot shared public exposure. Its current Flask routes have no evidenced authentication, authorization, or tenant boundary and include mutable content, upload, control, and interval endpoints.
- Cross-product session or password migration.
- Production deployment or domain cutover.

## Architecture Before

The products remain independently deployed systems with separate runtimes, databases, credentials, persistence models, and auth mechanisms:

| Product | Runtime | Current identity/tenant boundary |
|---|---|---|
| Gaatha Suite | FastAPI/ASGI with React/Vite | JWT/password, refresh-cookie, organization context, role dependencies; tenant coverage is incomplete and some legacy Flask surfaces remain |
| Gaatha POS | Flask/WSGI with server-rendered UI | Flask-Login sessions, password hashing, CSRF, permissions, restaurant association |
| Sentira | NestJS API with Next.js web and workers | JWT/Passport, organization context, roles/permissions, refresh/session records |
| PostPilot | Flask with HTML/JavaScript | No evidenced user auth, role model, organization boundary, or project boundary; SQLite/local files and in-process threads |

There was no shared canonical identity, organization/project/module context, audit contract, or common response envelope. The Phase 2 usage-event schema was the first shared billing-related contract.

## Architecture After

The target platform boundary is now documented and partially represented by additive schemas:

```text
GaathaCore identity
        |
  organization
        |
      project (optional where the product has no project concept)
        |
      module access + user permission
        |
  product adapter -> Suite | POS | Sentira | PostPilot
        |
  audit events + usage events -> future billing ledger
```

The products remain independent services and databases. The contracts are compatibility boundaries, not a directive to change existing response bodies or schemas.

## Identity Design

The canonical `User` represents a person who can access GaathaCore and contains a stable platform identifier, login identity reference, status, and timestamps. Product credentials remain product-owned during migration. Passwords are never copied between systems.

The official administrative identity is **Admin - Jaygiri Gosai**. The platform ownership/development identity is **Architect, Developer, Owner, Founder - Hardikkumar Gajjar**. These are documented ownership identities only. No fake credentials were created and no name is hardcoded into authorization logic.

The future platform identity record should be linked to product identities through explicit mapping records, for example `identity_links(user_id, service, service_user_id, status)`. Linking must be idempotent, auditable, and reversible.

## Organization Design

`Organization` is the fundamental tenant boundary. It owns memberships, projects, module access, usage attribution, billing references, and audit visibility. Every authenticated product request should resolve organization scope from trusted authentication context, never from an untrusted request body alone.

Potential platform-owned entities are `organizations` and `organization_members`. Product tables remain product-owned until a separately approved migration.

## Project Design

`Project` is an optional logical workspace under an organization. It is required only for resources that genuinely have project scope. Organization-owned resources, such as a platform billing setting or a product with no project concept, may use a null project context.

Future `projects` and `project_members` records must enforce organization ownership on both the project and membership. A project identifier from another organization must produce the product's approved `403` or non-disclosing `404` behavior.

## Module Design

The initial canonical identifiers are:

- `business_suite`
- `pos`
- `sentira`
- `postpilot`

Module access is an organization-level entitlement with a status such as `enabled`, `trial`, or `disabled`, optionally narrowed to a project. Access requires both an enabled organization/project module and an explicit user permission. Module existence alone never grants access.

The request context schema is in `contracts/context.v1.schema.json`. PostPilot remains disabled for shared exposure until its boundary is implemented and tested.

## RBAC

The common vocabulary is:

| Existing evidence | Canonical role | Rule |
|---|---|---|
| Suite `superadmin` | `platform_admin` | Protected platform administration; not granted by default |
| Suite `orgadmin`; verified Sentira owner/admin | `organization_owner` or `organization_admin` | Organization, membership, project, and enabled-module administration |
| Suite `manager`; POS manager/admin | `manager` | Product-operational permissions only |
| Suite `lead`; elevated POS staff | `staff` | Explicit operational permissions only |
| Sentira read/report roles; POS read-only users | `viewer` | Explicit read permissions only |
| Unverified or unmappable role | `unmapped` | No access until reviewed |

The canonical permission vocabulary includes:

`organization.read`, `organization.manage`, `project.read`, `project.manage`, `users.read`, `users.manage`, `billing.read`, `billing.manage`, `usage.read`, `business_suite.access`, `pos.access`, `sentira.access`, and `postpilot.access`.

This is a mapping and authorization design, not a production rename. Product-specific permissions remain in force until adapters translate and test them. Administrator privileges are not assigned by default.

## Authentication Mapping

| Product | Current mechanism | Phase 3 adapter strategy |
|---|---|---|
| Suite | JWT/password, refresh-cookie, organization context | Add identity-link and context adapter; preserve current sessions during transition |
| POS | Flask-Login/session and restaurant scope | Add gateway/session adapter after proving restaurant-to-organization mapping |
| Sentira | JWT/Passport, refresh/session records, organization RBAC | Add token/context adapter; retain existing rotation and revocation behavior |
| PostPilot | No evidenced authentication or tenant boundary | Keep internal or behind an authenticated gateway; implement boundary before shared exposure |

No passwords are migrated. Existing production sessions are not invalidated. A future cutover requires dual-read identity resolution, explicit session lifetime policy, replay protection, rollback, and an approved communication plan.

## PostPilot Security Boundary

Inspection found unauthenticated Flask endpoints for search, post listing/creation/update/deletion, uploads, start/stop controls, status, and interval mutation. The service also uses SQLite/local media and starts in-process background threads. Social provider clients and environment-level identifiers are present in the application surface.

Therefore this phase does not expose PostPilot through GaathaCore and does not run external social posting. Before exposure, PostPilot requires authenticated requests, organization/project ownership on posts/media/social-account records, encrypted service-owned provider credentials, authorization on every control endpoint, durable job ownership and idempotency, rate limits, secret redaction, and two-organization negative tests.

## API Contract

`contracts/api-envelope.v1.schema.json` defines:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

Error envelopes use `success: false`, `data: null`, and a structured error with one of `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, `RATE_LIMITED`, or `INTERNAL_ERROR`. Existing product APIs are not rewritten in this phase; adapters must preserve compatibility until clients are verified.

Common HTTP semantics are: 401 for missing/invalid auth, 403 for authenticated denial, 404 for inaccessible resources where existence should not leak, 409 for state conflicts, 422 for validation, 429 for rate limiting, and 500 for non-sensitive internal failures. Stack traces and credentials must never be returned.

## Request Correlation

`X-Request-ID` is the platform convention. An edge or service generates a non-sensitive ID when absent, preserves a valid incoming ID, propagates it to downstream calls, and includes it in response metadata and relevant logs. Existing Sentira correlation middleware remains authoritative until adapters are introduced. IDs must not contain tokens or personal secrets.

## Audit Architecture

`contracts/audit-event.v1.schema.json` defines an append-only event containing organization, optional project, optional user, module, action, resource type/id, timestamp, request ID, and non-sensitive metadata.

Examples include user creation, organization changes, role changes, invoice creation, POS completion, camera configuration, social-account connection, and billing-setting changes. Existing product audit systems are not replaced. Future adapters should emit a normalized event alongside existing product audit records, with an idempotency key or deterministic event identity to prevent duplicate imports.

## Usage/Billing Relationship

The existing `contracts/usage-event.v1.schema.json` remains the usage source contract. The intended relationship is:

```text
organization -> optional project -> module -> feature -> usage event -> pricing rule -> future ledger/charge
```

Every billable event is attributable to organization, optional project, module, feature, source service, quantity, unit, timestamp, and idempotency key. Audit records describe authorization and operational changes; usage events describe measurable consumption. They may reference each other by request/event IDs, but neither event type contains payment credentials.

No live payment provider, charge, invoice, wallet, credit balance, or billing enforcement was added.

## Database Strategy

The four product databases remain separate. Potential central records are users, organizations, memberships, projects, roles, permissions, module access, audit events, and usage events. Product-specific business data remains owned by Suite, POS, Sentira, or PostPilot.

No migration or database table was added in Phase 3. A future central database requires stable external IDs, mapping tables, idempotent synchronization, outbox/inbox delivery, reconciliation, backup/restore rehearsal, and a tested rollback checkpoint. Existing integer and UUID identifiers must be preserved rather than cosmetically converted.

## Tenant Isolation

The required enforcement chain is:

```text
trusted user -> organization membership -> optional project membership -> module access -> resource ownership
```

Required negative tests include two organizations and users attempting cross-organization project, invoice, POS order, Sentira event, and PostPilot social-account access; cross-project access without membership; and module access without the module permission. These tests must run against disposable test data only.

Phase 3 did not claim this matrix as passing. Suite and Sentira have partial tenant-scoped implementation and tests; POS has important restaurant-scoped routes; PostPilot has no acceptable boundary yet.

## Tests

Executed for this phase:

| Check | Result |
|---|---|
| Parse API envelope, context, audit, and usage JSON schemas with Node | PASS |
| `git diff --check` | PASS |
| PostPilot route/security surface inspection | PASS; confirmed boundary gap |

Previously recorded Phase 2 checks remain valid, including Python compilation, Sentira focused health test/lint, Suite frontend build, and the documented environment blocks for POS pytest and unsafe PostPilot smoke posting. No external social posts, customer emails, real charges, or VPS actions were performed.

## Security Findings

1. PostPilot is not safe for public shared exposure because mutable and control routes lack evidenced authentication and tenant enforcement.
2. Product credentials, JWT secrets, database URLs, social tokens, camera credentials, and storage credentials must remain service-scoped. No secret values are included here.
3. Suite and Sentira still need complete cross-tenant CRUD/IDOR evidence before identity federation.
4. Role mappings are not yet a substitute for product-specific authorization checks.
5. Usage and audit contracts are schemas only; append-only storage, retention, redaction, replay, and access controls remain future work.
6. Existing product response and error formats differ; an adapter or versioned endpoint is required before client migration.

## Files Changed

Phase 3 files added or updated by this work:

- `contracts/api-envelope.v1.schema.json`
- `contracts/context.v1.schema.json`
- `contracts/audit-event.v1.schema.json`
- `docs/GAATHACORE_PLATFORM_CONTRACTS.md`
- `GAATHACORE_PHASE_2_REPORT.md` (handoff addendum)
- `GAATHACORE_PHASE_3_REPORT.md`

The worktree also contains pre-existing Phase 1/2 changes and generated assets. They were preserved and are not attributed to this Phase 3 implementation. No product runtime source, production configuration, migration, or deployment file was changed by Phase 3.

## Migration Requirements

Future migration work must:

1. Define canonical identity-link, organization, project, role, permission, and module-access records.
2. Map Suite organizations, POS restaurants, Sentira organizations, and PostPilot ownership into explicit organizations without guessing.
3. Add adapters that resolve trusted context and preserve existing clients.
4. Add request-ID propagation and normalized audit/usage producers with idempotency.
5. Prove two-organization isolation across representative read/write/delete paths and realtime channels.
6. Secure PostPilot before registering it as an enabled module.
7. Rehearse database and object-storage backup/restore and migration rollback.

## VPS Implications

None in this phase. The VPS, reverse proxy, containers, domains, databases, volumes, certificates, and existing services were not touched. Future deployment needs private infrastructure networking, HTTPS at the edge, secret injection, health/readiness checks, backups, log redaction, resource limits, and a staged rollback plan. `app.gaatha.tech` versus `core.gaatha.tech` remains undecided.

## Rollback

The implemented changes are additive and can be rolled back by removing the new contract/document files and the Phase 2 handoff paragraph. No product runtime, data, session, credential, route, or deployment state depends on them yet. Future runtime adoption must use feature flags or versioned adapters, dual-read/dual-write only where reconciled, immutable event replay, and a tested checkpoint before any cutover.

## Unresolved Issues and Remaining Risks

- No central identity provider or canonical platform database exists.
- Organization mapping across restaurant/site/project concepts is undecided.
- Full tenant-negative coverage is incomplete.
- PostPilot needs a complete security boundary, durable jobs, and credential isolation.
- Product role semantics are not equivalent and require per-permission review.
- Audit retention, event delivery, data residency, and privacy policy are undecided.
- Billing pricing, tax, currency, ledger ownership, and payment authorization are future decisions.
- Common timestamp and ID conventions remain documented as compatibility concerns; existing IDs must be preserved.
- Docker and database runtime verification limits from Phase 2 remain relevant.

## Recommended Phase 4

### Phase 4 handoff addendum

Phase 4 implemented a minimal local Core platform layer in the workspace without touching any production database or product runtime. The new Core service introduces a SQLite-backed persistence layer for identity, organization membership, project membership, module access, RBAC, audit events, and usage ownership. This is still a platform foundation, not a production merge or a direct product rewrite.

#### IMPLEMENTED

- Core `User`, `Organization`, `Project`, and membership tables
- explicit role vocabulary and permission registry
- module access enforcement scoped to organization/project/module
- server-side tenant isolation checks
- append-oriented audit-event persistence
- usage ownership context that rejects cross-tenant attribution
- API envelope wrapper for identity responses

#### DESIGNED

- product-specific auth adapters for Suite, POS, Sentira, and PostPilot
- future migration to a production platform database
- persistent module configuration and policy structure
- richer audit retention and usage ledger patterns

#### BLOCKED

- public PostPilot exposure through the unified platform
- real billing or charging
- database merge
- production migration, VPS deployment, or service restart
- password/session migration or credential invalidation

#### FUTURE MIGRATION

- map Suite organizations, POS restaurants, Sentira sites, and PostPilot ownership into Core identities without guessing
- prove route-level cross-tenant denial with real negative tests
- adopt a formal platform database and approved migration plan
- implement product adapters before any live cutover

Phase 4 remains intentionally additive and reversible. It is safe to continue with product-specific adapter design, but not safe to expose public shared access or run a production migration.


Phase 4 should select and implement a disposable, non-production identity/organization registry with explicit external-ID mappings and adapter tests for one product first, preferably Suite or Sentira where organization context already exists. In parallel, add the cross-tenant negative test harness and define PostPilot's authenticated internal boundary. Do not enable central billing or perform a domain cutover until those controls pass in a rollback-tested environment.

## Final Classification

| Classification | Phase 3 result |
|---|---|
| Implemented now | Contract schemas, platform contract documentation, Phase 2 handoff, inspection evidence |
| Designed but not implemented | Canonical database, adapters, centralized RBAC/module gate, audit/usage storage, project mappings |
| Requires future migration | Identity federation, product tenant mapping, client envelope adoption, centralized event delivery |
| Blocked/unsafe | PostPilot shared exposure, live billing, password/session migration, VPS deployment, domain cutover |
