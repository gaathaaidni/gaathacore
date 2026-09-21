# API Error Catalog

**Status:** IMPLEMENTED for errors centralized by the active FastAPI app; route-specific errors require ongoing cataloging.

| Status | Code | Message/meaning | Diagnosis |
|---:|---|---|---|
| 401 | `HTTP_401` | Authentication is missing or invalid | Check bearer token, expiry, and user lookup |
| 403 | `HTTP_403` | Access is denied or organization context is missing | Check active user, role, and ownership |
| 404 | `HTTP_404` | Route or resource not found | Confirm active router and record scope |
| 409 | `HTTP_409` | Conflict; legal version may be unavailable | Check current published version/state |
| 422 | `VALIDATION_ERROR` | Request validation failed | Compare payload with the route schema |
| 500 | `INTERNAL_ERROR` | Generic server failure | Use timestamp and request context to inspect logs |
| 503 | response status `not_ready` | Database readiness failed | Check PostgreSQL connectivity and migrations |

Technical exception details should remain in logs. Existing route-level `HTTPException` messages may require normalization before a complete public catalog can be claimed.
