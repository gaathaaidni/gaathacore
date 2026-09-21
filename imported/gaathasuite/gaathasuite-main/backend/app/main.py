from contextlib import asynccontextmanager
from pathlib import Path
import logging
import re

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import Config
from app.db import engine
from app.models.user import User
from app.tasks.notifications import router as notifications_router
from app.preferences import router as preferences_router
from app.tasks.auth import router as tasks_auth_router
from app.routes.auth import router as auth_router
from app.routes.approvals import router as approvals_router
from app.routes.departments import router as departments_router
from app.tasks.import_export import router as import_export_router
from blueprints.ai_assistant.routes import ai_router as ai_assistant_router
from app.schemas.routes import router as settings_router
from app.schemas.vendor_invoices import router as vendor_invoices_router
from app.schemas.vendors import router as vendor_management_router
from app.routes.hr import router as hr_router
from app.routes.legal import router as legal_router
from app.utils.downloads import router as downloads_router
from app.utils.dependencies import get_db, get_current_user
from blueprints.crm.routes import router as legacy_crm_router
from blueprints.crm.routes_refactored import router as crm_router
from blueprints.inventory.routes import router as inventory_router
from blueprints.books.routes_refactored import router as books_router
from blueprints.expenses.routes_refactored import router as expenses_router
from app.routes.transactions import router as transactions_router
from core.platform import GaathaCoreService
from core.suite_adapter import SuiteCoreAdapter, suite_role_to_core_role

logger = logging.getLogger(__name__)
static_dir = Path(__file__).resolve().parents[1] / "static"
if not static_dir.exists():
    static_dir = Path(__file__).resolve().parents[2] / "frontend" / "static"
SENSITIVE_PATH_PATTERNS = (
    re.compile(r"^/\.git(?:/|$)", re.IGNORECASE),
    re.compile(r"^/\.env(?:\..*)?$", re.IGNORECASE),
    re.compile(r"^/\.aws(?:/|$)", re.IGNORECASE),
    re.compile(r"^/terraform\.tfstate(?:\..*)?$", re.IGNORECASE),
    re.compile(r"^/docker-compose\.ya?ml.*$", re.IGNORECASE),
    re.compile(r"^/backup.*$", re.IGNORECASE),
    re.compile(r".*\.(?:bak|backup|sql)$", re.IGNORECASE),
    re.compile(r"^/(?:requirements\.txt|package\.json|Dockerfile|\.gitignore)$", re.IGNORECASE),
)


def is_sensitive_path(path: str) -> bool:
    return any(pattern.match(path) for pattern in SENSITIVE_PATH_PATTERNS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Config.validate_required()
    yield
    await engine.dispose()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), geolocation=(), microphone=(), payment=()",
        )
        return response


app = FastAPI(
    title="GaathaSuite API",
    description="API for GaathaSuite business management platform",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in (Config.CORS_ORIGINS or "").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={"error": {"code": f"HTTP_{exc.status_code}", "message": detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )


app.include_router(notifications_router, prefix="/api/v1")
app.include_router(preferences_router, prefix="/api/v1")
app.include_router(tasks_auth_router)
app.include_router(auth_router)
app.include_router(approvals_router)
app.include_router(import_export_router, prefix="/api/v1")
app.include_router(ai_assistant_router, prefix="/api/v1")
app.include_router(downloads_router, prefix="/api/v1")
app.include_router(settings_router)
app.include_router(vendor_invoices_router)
app.include_router(vendor_management_router)
app.include_router(hr_router)
app.include_router(departments_router)
app.include_router(legal_router)
app.include_router(legacy_crm_router)
app.include_router(crm_router)
app.include_router(inventory_router)
app.include_router(books_router)
app.include_router(expenses_router)
app.include_router(transactions_router)

core_service = GaathaCoreService(database_path=str(Path(__file__).resolve().parents[3] / "gaathacore.db"))
suite_adapter = SuiteCoreAdapter(service=core_service)


@app.get("/api/core/identity")
async def suite_core_identity(
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    # Keep Suite auth authoritative while mapping into the Core identity/tenant boundary.
    suite_user_id = current_user.id
    suite_org_id = getattr(current_user, "organization_id", None)
    if suite_org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization context is required")

    mapped_user = core_service.resolve_core_user_for_suite_user(suite_user_id)
    if mapped_user is None:
        core_user = core_service.create_user(
            email=current_user.email,
            username=current_user.username,
            display_name=getattr(current_user, "first_name", None) or current_user.username,
            status="active",
        )
        core_service.map_suite_user(suite_user_id=suite_user_id, core_user_id=core_user["id"])
        mapped_user = core_user["id"]

    mapped_org = core_service.resolve_core_organization_for_suite_organization(suite_org_id)
    if mapped_org is None:
        org = core_service.get_organization_by_slug(str(suite_org_id))
        if org is None:
            org = core_service.create_organization(name=f"Suite Org {suite_org_id}", slug=f"suite-org-{suite_org_id}", status="active")
        core_service.map_suite_organization(suite_organization_id=suite_org_id, core_organization_id=org["id"])
        core_service.set_module_access(organization_id=org["id"], project_id=None, module_key="suite", enabled=True)
        mapped_org = org["id"]

    org_membership = core_service._get_organization_membership(mapped_user, mapped_org)
    if org_membership is None:
        core_service.add_organization_membership(
            user_id=mapped_user,
            organization_id=mapped_org,
            role=suite_role_to_core_role(getattr(current_user, "role", "user")),
            status="active",
        )
    if not core_service.module_access_enabled(organization_id=mapped_org, project_id=None, module_key="suite"):
        core_service.set_module_access(organization_id=mapped_org, project_id=None, module_key="suite", enabled=True)

    project_id = None
    suite_project_id = getattr(current_user, "project_id", None)
    if suite_project_id is not None:
        project = suite_adapter.ensure_project_scope(
            suite_organization_id=suite_org_id,
            suite_project_id=suite_project_id,
            core_project_name=f"Suite Project {suite_project_id}",
            core_project_slug=f"suite-project-{suite_project_id}",
        )
        project_id = project["id"]

    identity = suite_adapter.resolve_authenticated_request(
        suite_user_id=suite_user_id,
        suite_organization_id=suite_org_id,
        suite_project_id=suite_project_id,
        module_key="suite",
        module_permissions={"suite": ["module.read", "project.read", "organization.read"]},
        request_id=(request.headers.get("X-Request-ID") if request else None),
    )

    return {
        "success": True,
        "data": {
            "current_user": identity["current_user"],
            "current_organization": identity["current_organization"],
            "current_project": identity["current_project"],
            "current_module": identity["current_module"],
            "permissions": identity["permissions"],
            "organization": identity["organization"],
            "project": identity["project"],
            "request_id": identity["request_id"],
            "user": identity["user"],
        },
        "error": None,
        "meta": {"request_id": identity["request_id"], "scope": "suite"},
    }


@app.get("/health", include_in_schema=False)
@app.get("/_health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


@app.get("/api/v1/health", include_in_schema=False)
async def versioned_health_check():
    return {
        "service": "gaatha-suite",
        "status": "healthy",
        "dependencies": {"database": "unknown"},
    }


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness database check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "dependencies": {"database": "unavailable"}},
        )
    return {"status": "ready", "dependencies": {"database": "available"}}


@app.get("/api/dashboard-stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    async def count_rows(table: str) -> int:
        try:
            result = await db.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE organization_id = :organization_id"),
                {"organization_id": org_id},
            )
            return int(result.scalar_one())
        except SQLAlchemyError:
            await db.rollback()
            return 0

    async def scalar_value(query: str, default=0):
        try:
            result = await db.execute(text(query), {"organization_id": org_id})
            return result.scalar_one() or default
        except SQLAlchemyError:
            await db.rollback()
            return default

    revenue = await scalar_value(
        "SELECT COALESCE(SUM(total_amount), 0) FROM invoice "
        "WHERE organization_id = :organization_id AND status != 'cancelled'"
    )
    low_stock = await scalar_value(
        "SELECT COUNT(*) FROM stock_record "
        "WHERE organization_id = :organization_id AND quantity < 0"
    )

    return {
        "customers": await count_rows("customers"),
        "invoices": await count_rows("invoice"),
        "products": await count_rows("items"),
        "employees": await count_rows("employee"),
        "total_revenue": revenue,
        "low_stock_count": low_stock,
        "recent_activity": [],
    }


if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    frontend_index = static_dir / "dist" / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        request_path = f"/{full_path}"
        if (
            is_sensitive_path(request_path)
            or full_path in {"api", "health", "_health", "ready"}
            or full_path.startswith("api/")
        ):
            raise HTTPException(status_code=404, detail="Not found")
        if frontend_index.exists():
            return FileResponse(frontend_index)
        raise HTTPException(status_code=404, detail="Frontend build not found")
