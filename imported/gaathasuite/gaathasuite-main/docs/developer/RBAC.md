# Role-Based Access Control

**Status:** PARTIALLY IMPLEMENTED / NOT YET VERIFIED route-wide.

The FastAPI stack has canonical-role handling and dependency helpers such as `require_roles`, plus explicit organization context and superadmin restrictions. The legacy Flask stack has separate RBAC middleware. These are not equivalent permission systems.

| Control | Current evidence | Verification status |
|---|---|---|
| Authentication | JWT bearer resolution and session-cookie WebSocket resolution | IMPLEMENTED, targeted tests exist |
| Organization membership | `User.organization_id` and organization dependency | IMPLEMENTED in foundation paths |
| Role checks | Canonical role dependency helpers | IMPLEMENTED, incomplete matrix coverage |
| Superadmin escalation protection | Organization admins cannot assign `superadmin` in tested path | VERIFIED in foundation test |
| Resource ownership | Route-specific filters | PARTIAL |
| Delete/export/approval permissions | Route-specific and incomplete audit | NOT YET VERIFIED |

Do not describe the product as having complete RBAC until the endpoint matrix and negative tests are complete.
