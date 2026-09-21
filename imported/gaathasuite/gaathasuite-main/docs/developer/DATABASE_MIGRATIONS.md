# Database Migrations

**Status:** IMPLEMENTED / upgrade verification environment-dependent.

Use Alembic, not ad hoc schema edits:

```bash
cd backend
alembic -c migrations/alembic.ini upgrade head
alembic -c migrations/alembic.ini check
alembic -c migrations/alembic.ini heads
```

Before production: back up PostgreSQL, review the migration and merge heads, apply it to staging, verify health and tests, then apply it during the release window. Downgrades require a tested rollback plan; do not assume destructive reversibility.
