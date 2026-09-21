# Database

**Status:** IMPLEMENTED BUT NOT FULLY VERIFIED.

PostgreSQL is the required database. SQLAlchemy 2 async engine/session code is under `backend/app/db.py`; shared models are under `backend/app/models/`. Alembic migrations are under `backend/migrations`.

Major model areas include users, organizations, legal documents/acceptances, approvals, departments, HR, inventory, finance/books, CRM, expenses, procurement, vendors, invoices, notifications, preferences, and assets. Many records carry organization ownership, but invariants and route-wide tenant protection need continued testing.

Never place credentials in this document or migration files.
