# API Reference

**Status:** PARTIALLY IMPLEMENTED; generated OpenAPI remains the preferred detailed reference.

FastAPI exposes OpenAPI from the active application. Important registered surfaces include authentication, approvals, departments, HR, legal documents and acceptances, notifications, preferences, imports/exports, AI assistant, downloads, vendor management, vendor invoices, and settings. The dashboard endpoint is `/api/dashboard-stats`; health endpoints are `/health`, `/_health`, and `/ready`.

Authentication is generally bearer JWT through `/auth/token` or related auth routes. Exact request and response schemas must be read from the route modules and OpenAPI for the deployed version.

Known structured errors from `backend/app/main.py`:

| HTTP | Code | Meaning |
|---:|---|---|
| 401 | `HTTP_401` | Authentication is missing or invalid |
| 403 | `HTTP_403` | Authenticated caller lacks access |
| 404 | `HTTP_404` | Resource or route was not found |
| 409 | `HTTP_409` | Conflict, including unavailable legal version |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 500 | `INTERNAL_ERROR` | Unexpected server error; details are logged server-side |

Individual route errors may still use FastAPI exception details. See [API Error Catalog](API_ERROR_CATALOG.md).
