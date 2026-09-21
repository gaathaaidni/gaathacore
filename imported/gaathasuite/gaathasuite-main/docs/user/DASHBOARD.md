# Dashboard

**Status:** IMPLEMENTED in the active API; frontend workflow NOT YET VERIFIED.

The dashboard statistics endpoint returns organization-scoped counts for customers, invoices, products, employees, revenue, low-stock records, and a recent-activity field. The API is `/api/dashboard-stats` and requires authentication plus an organization association.

The dashboard values should be treated as operational summaries, not as independently audited financial statements.
