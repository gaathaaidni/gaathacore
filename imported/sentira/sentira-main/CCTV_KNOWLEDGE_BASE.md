# CCTV Knowledge Base

The knowledge base is backend-driven. Public catalog reads are available through `/api/cctv/manufacturers`, `/api/cctv/manufacturers/:id/models`, `/api/cctv/models/:id/guides`, and `/api/cctv/help/search?q=...`.

Compatibility is represented per model in `supportedProtocols` with a status of `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNKNOWN`, `NOT_SUPPORTED`, or `REQUIRES_ASSISTANCE`, plus `verified` and notes. Unknown is not treated as unsupported.

Guides contain simple steps (`TEXT`, `CHOICE`, `TIP`, `WARNING`, `INPUT`, `TEST`, `SUCCESS`, and `FAILURE`) and troubleshooting branches. Do not put passwords or permanent credentials in guide content.

Administrators with `system.admin` may create manufacturers, models, and guides through:

- `POST /api/cctv/admin/manufacturers`
- `POST /api/cctv/admin/models`
- `POST /api/cctv/admin/guides`

Seed data is intentionally generic and unverified. Model-specific compatibility should be added only after verification.
