# ADR 0002: PostgreSQL and Alembic

- **Status:** Accepted
- **Context:** Runtime data access uses SQLAlchemy async sessions and schema history is maintained under `backend/migrations`.
- **Decision:** Use PostgreSQL as the supported database and Alembic for schema changes.
- **Alternatives:** SQLite production use; ad hoc SQL changes.
- **Consequences:** Real PostgreSQL is required for meaningful tests and migration verification.
