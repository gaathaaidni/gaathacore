# Multi-Tenancy

**Status:** PARTIAL.

`User.organization_id` is the primary tenant association observed in the active foundation. Dashboard queries and organization-admin user management apply organization scope. The foundation test proves one dashboard isolation scenario.

Every route, relationship, export, download, background task, and legacy endpoint still needs direct ownership review. A client-provided organization ID is untrusted until the server validates membership and ownership. See [Tenant Isolation](../security/TENANT_ISOLATION.md).
