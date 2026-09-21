# Development Setup

**Status:** IMPLEMENTED from repository scripts.

Prerequisites: Python compatible with CI (3.11), Node 18 for CI parity, PostgreSQL 15-compatible database, and Docker Compose for the container path.

```bash
cp backend/.env.example backend/.env
# Set DATABASE_URL and SECRET_KEY.
cd backend
alembic -c migrations/alembic.ini upgrade head
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 5051
```

Frontend commands:

```bash
npm install --prefix frontend
npm run dev --prefix frontend
npm run build --prefix frontend
```

Do not commit `.env` files. The Docker path remains `docker compose up --build`.
