# Gaatha Suite

## Professional Business Management SaaS

Gaatha Suite is a business management platform for centralizing operational information across organizations. The public beta is available at [gaathasuite.gaatha.tech](https://gaathasuite.gaatha.tech).

Architected and developed by **Hardikkumar Gajjar**.

The repository is the source of truth. Current implementation status is **PARTIAL / IMPLEMENTED BUT NOT FULLY VERIFIED**. Some business modules and legacy routes are present in source but are not yet verified as complete production workflows.

## Current technology

- **Frontend:** React 18, React Router, Vite, Tailwind CSS
- **Backend:** FastAPI, Uvicorn/Gunicorn
- **Data:** PostgreSQL, SQLAlchemy 2 async sessions, Alembic migrations
- **Supporting services:** Redis configuration and Pub/Sub integrations; worker deployment is not currently verified
- **Deployment:** Docker, Compose, Render, Nginx, and Kubernetes manifests
- **Security foundation:** JWT authentication, role dependencies, organization identifiers, structured errors, and baseline security headers

## Start locally

```bash
cp backend/.env.example backend/.env
# Configure the required values in backend/.env.
docker compose up --build
```

For host-based development and the authoritative configuration details, see [SETUP.md](SETUP.md) and [docs/developer/DEVELOPMENT_SETUP.md](docs/developer/DEVELOPMENT_SETUP.md).

## Documentation

- [Documentation home](docs/README.md)
- [Product information](docs/product/PRODUCT_INFORMATION.md)
- [Current limitations](docs/product/CURRENT_LIMITATIONS.md)
- [User manual](docs/user/GETTING_STARTED.md)
- [Administrator guide](docs/admin/ADMIN_GUIDE.md)
- [Developer architecture](docs/developer/ARCHITECTURE.md)
- [Configuration reference](docs/developer/CONFIGURATION.md)
- [Security overview](docs/security/SECURITY_OVERVIEW.md)
- [Production operations](docs/operations/PRODUCTION_CONFIGURATION.md)
- [Legal foundation](docs/legal/LEGAL_ENTITY_CONFIGURATION.md)
- [Release checklist](docs/release/RELEASE_CHECKLIST.md)
- [Professionalization report](GAATHA_SUITE_PROFESSIONALIZATION_REPORT.md)

## Repository boundaries

The active runtime is `backend/app/main.py`, exported through `backend/main.py`. The React application is under `frontend/`. The `backend/blueprints/` tree contains legacy and transition Flask-style modules; its presence does not prove that every module is mounted in the active FastAPI runtime.

Do not commit environment files or secrets. Production deployment must keep PostgreSQL and Redis private and provide required settings through deployment configuration.

## Verification

Useful checks include:

```bash
python -m compileall -q backend
python -m pytest backend/tests
npm --prefix frontend run build
git diff --check
```

The backend tests require an isolated PostgreSQL database through `TEST_DATABASE_URL`. Results must be recorded as verified only when the command has actually run successfully in the target environment.

## Support, security, and legal status

Support, security reporting, privacy, and legal documents are documented under [docs/](docs/). Legal documents are foundational templates and require qualified legal review. No certification, regulatory compliance, or final contracting entity is asserted by this repository.
