# Access Control

**Status:** PARTIALLY IMPLEMENTED / NOT YET VERIFIED.

FastAPI dependencies provide authenticated-user resolution, organization context, canonical-role checks, and explicit superadmin/organization-admin behavior. JWT access tokens are used by bearer-authenticated routes; WebSocket authentication uses a session cookie.

A complete endpoint-by-endpoint permission matrix is not yet established. Role names and behavior must be read from `backend/app/utils/roles.py`, `backend/app/utils/dependencies.py`, route dependencies, and the legacy Flask middleware before customer-facing guarantees are made.

## Minimum authorization rule

Authentication proves who the caller is. It does not prove that the caller may access a requested organization or record. Every resource operation must validate organization ownership and the caller's role or permission.

See [RBAC](../developer/RBAC.md) and [Security Gap Register](SECURITY_GAP_REGISTER.md).
