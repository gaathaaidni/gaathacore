# Testing

**Status:** PARTIALLY IMPLEMENTED.

CI runs Ruff, frontend linting, PostgreSQL-backed Alembic migrations, backend pytest with coverage, and the frontend production build. Existing backend tests cover auth, inactive users, malformed tokens, basic dashboard tenant scoping, superadmin escalation, model assertions, and HR organization columns.

Missing or incomplete coverage includes frontend tests, route-wide tenant IDOR tests, full permission matrix tests, upload security, worker execution, payment webhooks, migration downgrade/upgrade scenarios, and end-to-end business workflows.

```bash
python -m pytest backend/tests
npm run lint --prefix frontend
npm run build --prefix frontend
```
