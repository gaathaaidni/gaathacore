from __future__ import annotations

from typing import Any, Dict, Optional

from core.platform import (
    GaathaCoreService,
    PermissionDeniedError,
    ResourceScopeError,
    _normalize_module_key,
)
from core.factory import create_core_service


def suite_role_to_core_role(role: Any) -> str:
    normalized = str(role or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "superadmin": "platform_admin",
        "super_admin": "platform_admin",
        "orgadmin": "organization_admin",
        "org_admin": "organization_admin",
        "organization_admin": "organization_admin",
        "organization_owner": "organization_owner",
        "owner": "organization_owner",
        "manager": "manager",
        "lead": "manager",
        "auditor": "viewer",
        "partner": "viewer",
        "standard_user": "viewer",
        "standarduser": "viewer",
        "user": "viewer",
        "member": "viewer",
        "viewer": "viewer",
        "staff": "staff",
        "project_admin": "project_admin",
        "projectadmin": "project_admin",
    }
    return mapping.get(normalized, "viewer")


class SuiteCoreAdapter:
    def __init__(self, service: Optional[GaathaCoreService] = None):
        self.core = service or create_core_service()

    def ensure_suite_mapping(self, *, suite_user_id: Any = None, core_user_id: str = None, suite_organization_id: Any = None, core_organization_id: str = None) -> Dict[str, Any]:
        if suite_user_id is not None and core_user_id is not None:
            return self.core.map_suite_user(suite_user_id=suite_user_id, core_user_id=core_user_id)
        if suite_organization_id is not None and core_organization_id is not None:
            return self.core.map_suite_organization(suite_organization_id=suite_organization_id, core_organization_id=core_organization_id)
        raise ValueError("Provide suite-user/core-user or suite-org/core-org mapping values")

    def ensure_org_membership(self, *, suite_user_id: Any, suite_organization_id: Any, core_role: Optional[str] = None) -> Dict[str, Any]:
        core_user_id = self.core.resolve_core_user_for_suite_user(suite_user_id)
        if core_user_id is None:
            raise PermissionDeniedError("Suite user is not mapped to a Core user")
        core_org_id = self.core.resolve_core_organization_for_suite_organization(suite_organization_id)
        if core_org_id is None:
            raise ResourceScopeError("Suite organization is not mapped to a Core organization")
        membership = self.core._get_organization_membership(core_user_id, core_org_id)
        mapped_role = suite_role_to_core_role(core_role or "viewer")
        if membership is None:
            return self.core.add_organization_membership(user_id=core_user_id, organization_id=core_org_id, role=mapped_role, status="active")
        if membership["status"] != "active":
            raise PermissionDeniedError("Organization membership is inactive")
        return membership

    def ensure_project_scope(self, *, suite_organization_id: Any, suite_project_id: Any, core_project_name: str, core_project_slug: Optional[str] = None) -> Dict[str, Any]:
        core_org_id = self.core.resolve_core_organization_for_suite_organization(suite_organization_id)
        if core_org_id is None:
            raise ResourceScopeError("Suite organization must map to a Core organization before project scope can be validated")
        existing = self.core.resolve_core_project_for_suite_project(suite_organization_id=suite_organization_id, suite_project_id=suite_project_id)
        if existing is not None:
            project = self.core.get_project(existing)
            if project is not None:
                return project
        slug = (core_project_slug or core_project_name).strip().lower().replace(" ", "-")
        project = self.core.get_project_by_slug(core_org_id, slug)
        if project is None:
            project = self.core.create_project(organization_id=core_org_id, name=core_project_name, slug=slug, project_type="business")
        self.core.map_suite_project(suite_organization_id=suite_organization_id, suite_project_id=suite_project_id, core_project_id=project["id"])
        return project

    def enable_module(self, *, organization_id: str, project_id: Optional[str], module_key: str = "suite", enabled: bool = True) -> Dict[str, Any]:
        return self.core.set_module_access(organization_id=organization_id, project_id=project_id, module_key=module_key, enabled=enabled)

    def resolve_authenticated_request(
        self,
        *,
        suite_user_id: Any,
        suite_organization_id: Any,
        suite_project_id: Optional[Any] = None,
        module_key: str = "suite",
        module_permissions: Optional[Dict[str, list[str]]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        request_id = request_id or "req-core-" + str(abs(hash(str(suite_user_id) + str(suite_organization_id))))
        core_user_id = self.core.resolve_core_user_for_suite_user(suite_user_id)
        if core_user_id is None:
            raise PermissionDeniedError("Suite user has no Core identity mapping")
        core_organization_id = self.core.resolve_core_organization_for_suite_organization(suite_organization_id)
        if core_organization_id is None:
            raise ResourceScopeError("Suite organization has no Core organization mapping")

        user = self.core.get_user(core_user_id)
        if user is None or user["status"] != "active":
            raise PermissionDeniedError("Core user is unknown or inactive")

        org = self.core.get_organization(core_organization_id)
        if org is None or org["status"] != "active":
            raise PermissionDeniedError("Core organization is inactive or missing")

        if suite_project_id is not None:
            mapped_project = self.core.resolve_core_project_for_suite_project(suite_organization_id=suite_organization_id, suite_project_id=suite_project_id)
            if mapped_project is not None:
                project = self.core.get_project(mapped_project)
                if project is not None and project["organization_id"] != core_organization_id:
                    raise ValueError("Requested Suite project does not belong to the authenticated organization")

        if suite_project_id is not None:
            with self.core._connect() as connection:
                project_rows = self.core._fetch_all(
                    connection,
                    "SELECT * FROM suite_project_map WHERE suite_project_id = ?",
                    (str(suite_project_id),),
                )
            for row in project_rows:
                project = self.core.get_project(row["core_project_id"])
                if project is not None and project["organization_id"] != core_organization_id:
                    raise ValueError("Requested Suite project does not belong to the authenticated organization")

        membership = self.core._get_organization_membership(core_user_id, core_organization_id)
        if membership is None or membership["status"] != "active":
            raise PermissionDeniedError("Suite user is not active in the mapped Core organization")

        # Bound by the authenticated Suite organization. Do not trust the caller-supplied org ID.
        if self.core.resolve_core_organization_for_suite_organization(suite_organization_id) != core_organization_id:
            raise ValueError("Requested Suite organization does not match the authenticated user organization")

        core_project_id = None
        if suite_project_id is not None:
            mapped_project = self.core.resolve_core_project_for_suite_project(suite_organization_id=suite_organization_id, suite_project_id=suite_project_id)
            if mapped_project is None:
                raise ResourceScopeError("Suite project has no mapped Core project")
            core_project_id = mapped_project
            project = self.core.get_project(core_project_id)
            if project is None or project["organization_id"] != core_organization_id:
                raise ResourceScopeError("Project is not in the mapped organization")

        self.core.require_scope(user_id=core_user_id, organization_id=core_organization_id, project_id=core_project_id, module_key=module_key)
        permissions = self.core._effective_permissions(user_id=core_user_id, organization_id=core_organization_id, project_id=core_project_id)

        if module_permissions:
            required = module_permissions.get(_normalize_module_key(module_key), [])
            missing = [perm for perm in required if perm not in permissions]
            if missing:
                raise PermissionDeniedError(f"Missing required permissions for module '{module_key}': {', '.join(missing)}")

        if module_key is not None:
            target_module = _normalize_module_key(module_key)
            if not self.core.module_access_enabled(organization_id=core_organization_id, project_id=core_project_id, module_key=target_module):
                raise PermissionDeniedError(f"Module '{target_module}' is not enabled for this scope")

        return {
            "current_user": core_user_id,
            "current_organization": core_organization_id,
            "current_project": core_project_id,
            "current_module": _normalize_module_key(module_key),
            "permissions": permissions,
            "request_id": request_id,
            "user": user,
            "organization": org,
            "project": self.core.get_project(core_project_id) if core_project_id else None,
        }
