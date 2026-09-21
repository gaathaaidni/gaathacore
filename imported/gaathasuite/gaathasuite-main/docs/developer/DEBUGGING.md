# Debugging

**Status:** IMPLEMENTED as an engineering procedure.

For a customer report: identify organization and role, reproduce the visible action, confirm the frontend request, locate the registered API route, inspect auth and organization scope, verify record ownership, inspect logs by timestamp, inspect database state safely, add a regression test, run focused checks, deploy through the release process, and verify health plus the affected workflow.

First determine whether the request is FastAPI (`backend/app`) or legacy Flask (`backend/blueprints`).
