# Multi-Tenancy Foundation

Authenticated users carry an `organization_id`, and the dashboard endpoint scopes all database counts and aggregates by the current user's organization. Organization-admin user management is scoped to the administrator's organization; superadmin access is explicit.

The Phase 2 API test foundation includes two organizations and verifies that a customer created for Organization A is not counted in Organization B's dashboard response. The test requires an isolated PostgreSQL database through `TEST_DATABASE_URL`.

This is not a complete tenant-isolation proof. Every tenant-owned route and model still requires a route-by-route audit, direct cross-tenant read/update/delete tests, and review of legacy Flask routes before production claims are possible.
