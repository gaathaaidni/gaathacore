# Gaatha Suite Documentation

**Status:** IMPLEMENTED / documentation foundation in progress  
**Last verified:** 2026-09-11 against the repository source

Gaatha Suite is a business management SaaS product. This documentation distinguishes current code from recommendations and does not assert unsupported features, compliance, or legal ownership.

## Start here

- [Product information](product/PRODUCT_INFORMATION.md)
- [Current limitations](product/CURRENT_LIMITATIONS.md)
- [Getting started](user/GETTING_STARTED.md)
- [Administrator guide](admin/ADMIN_GUIDE.md)
- [Architecture](developer/ARCHITECTURE.md)
- [Configuration](developer/CONFIGURATION.md)
- [API reference](developer/API.md)
- [Security overview](security/SECURITY_OVERVIEW.md)
- [Production configuration](operations/PRODUCTION_CONFIGURATION.md)
- [Legal entity configuration](legal/LEGAL_ENTITY_CONFIGURATION.md)
- [Release checklist](release/RELEASE_CHECKLIST.md)

## Status vocabulary

`IMPLEMENTED`, `VERIFIED`, `PARTIALLY IMPLEMENTED`, `NOT YET VERIFIED`, `PLANNED`, `REQUIRES LEGAL REVIEW`, and `REQUIRES BUSINESS CONFIRMATION` are used consistently throughout these pages.

## Source of truth

The active API is registered in `backend/app/main.py`; `backend/main.py` is a compatibility export. The React/Vite application is under `frontend/`. Legacy Flask-style modules under `backend/blueprints/` are documented as legacy unless mounted by the active application.
