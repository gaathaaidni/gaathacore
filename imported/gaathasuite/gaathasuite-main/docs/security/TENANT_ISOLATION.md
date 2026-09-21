# Tenant Isolation

**Status:** PARTIALLY IMPLEMENTED / NOT YET VERIFIED route-wide.

Authenticated users have an `organization_id`. The dashboard endpoint scopes counts and aggregates by the current user's organization, and organization-admin user management is scoped to that organization. The foundation test verifies a basic dashboard separation case.

The repository does not yet prove that every active route, legacy route, export, download, upload, WebSocket, and background task enforces ownership. Client-supplied organization IDs must never be trusted without server-side membership and ownership validation.

## Required review sequence

1. Resolve the authenticated user server-side.
2. Derive organization context from the authenticated user or authorized administrator.
3. Filter reads by organization ownership.
4. Apply the same scope to updates and deletes.
5. Verify related objects belong to the same organization.
6. Scope files, exports, jobs, and WebSocket channels.
7. Add direct cross-tenant read/update/delete tests.

Known evidence and gaps are recorded in [docs/MULTI_TENANCY.md](../MULTI_TENANCY.md) and [Security Gap Register](SECURITY_GAP_REGISTER.md).
