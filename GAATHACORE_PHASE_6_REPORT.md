# GAATHACORE Phase 6 Report

**Phase:** 6 - POS Adapter Proof and Real Restaurant-Scoped Tenant Enforcement
**Date:** 2026-09-21
**Workspace:** `/workspaces/gaathacore`
**Status:** Completed a workspace-safe POS proof that maps the real Gaatha POS restaurant boundary into Core project scope without altering POS auth, session, or production deployment behavior.

## 1. Objective

Prove that the materially different Gaatha POS architecture can be constrained by Core identity, tenant, project, and module boundaries without replacing POS login, merging product data, or claiming production federation.

## 2. Scope kept safe

- Core remains a local SQLite platform service.
- POS remains authoritative for JWT/session-style Flask auth and restaurant ownership.
- The actual POS tenant boundary is treated as a restaurant-scoped tenant, not as a direct organization surrogate.
- No production migration, DB merge, encryption migration, deploy, DNS, VPS, or SaaS federation was performed.
- Route protection remains additive and isolated to the Core access boundary.

## 3. Grounded architecture findings

This phase was grounded in the imported real POS app and its actual model shape:

- [imported/gaathapos/gaathapos-main/models.py](imported/gaathapos/gaathapos-main/models.py) contains a restaurant-scoped multi-tenant model.
- The POS app does not expose a separate organization table as the principal tenant unit.
- Restaurant ownership and access are mediated by `User.restaurant_id` and `Restaurant.owner_id`.
- The safe Core mapping is therefore: `POS Restaurant -> Core Project` and `POS User -> Core User`, with Core organization membership used as a higher-level organizational grouping only when explicitly mapped.

This is distinct from the Suite model and therefore requires a different adapter semantics rather than a direct copy of the Suite proof.

## 4. Implementation summary

The proof was implemented in:

- [core/pos_adapter.py](core/pos_adapter.py)
- [core/platform.py](core/platform.py)
- [tests/test_pos_adapter_phase6.py](tests/test_pos_adapter_phase6.py)

The implementation includes:

- mapping from POS user to Core user via `map_pos_user()`
- mapping from POS restaurant to Core organization/project via `map_pos_restaurant()`
- Core project/organization membership enforcement before route acceptance
- module enablement checks for the `pos` module
- rejection of cross-restaurant or cross-tenant access even when IDs are supplied by a client
- route-level enforcement using the real POS blueprint decorator and request lifecycle

## 5. Verified behavior

The focused proof command passed:

`cd /workspaces/gaathacore && pytest tests/test_core_phase4.py tests/test_suite_adapter_phase5.py tests/test_pos_adapter_phase6.py -q`

Result: `22 passed in 4.96s`.

This verifies:

- Core identity resolution remains valid.
- Suite adapter proof remains valid.
- POS user-to-Core identity mapping works.
- POS restaurant-to-Core project mapping works.
- cross-tenant restaurant access is rejected.
- disabled module access is rejected.
- real POS route protection uses the Core boundary without replacing native POS auth.

## 6. Remaining boundary conditions

- No production federation claim is made.
- No production deployment or DNS changes were made.
- No database merge or credential migration was performed.
- The adapter remains additive and intentionally workspace-local.
- Future expansion beyond this proof requires explicit approval and a staged migration plan.

## 7. Handoff

The workspace now contains a credible Phase 6 proof that POS can keep its own native auth and tenant model while being constrained by Core identity, restaurant/project scope, and module enablement. The pattern is intentionally additive, reversible, and does not presume a shared production core architecture.

## Phase 7 handoff

Phase 7 establishes a separate PostgreSQL Core architecture with Core-only migrations and preserves the POS and Suite product databases. SQLite remains explicit test/development scaffolding, while production selection requires `CORE_DATABASE_URL`. PostgreSQL execution against an isolated local database is still BLOCKED until that environment is supplied; no VPS, production migration, user migration, billing, commit, or push was performed. See `GAATHACORE_PHASE_7_REPORT.md`.
