from __future__ import annotations

import os
from functools import wraps
from typing import Any, Dict, Optional

from flask import g, request
from flask_login import current_user

from core.platform import (
    GaathaCoreService,
    PermissionDeniedError,
    ResourceScopeError,
    _normalize_module_key,
    _normalize_role,
)
from core.factory import create_core_service


def pos_role_to_core_role(role: Any) -> str:
    normalized = str(role or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "super_admin": "platform_admin",
        "superadmin": "platform_admin",
        "restaurant_admin": "organization_admin",
        "restaurantadmin": "organization_admin",
        "owner": "organization_owner",
        "admin": "organization_admin",
        "manager": "manager",
        "cashier": "staff",
        "waiter": "staff",
        "kitchen": "staff",
        "staff": "staff",
        "viewer": "viewer",
    }
    return mapping.get(normalized, "viewer")


class POSCoreAdapter:
    def __init__(self, service: Optional[GaathaCoreService] = None):
        self.core = service or create_core_service()

    def map_pos_user(self, *, pos_user_id: Any, core_user_id: str) -> Dict[str, Any]:
        return self.core.map_pos_user(pos_user_id=pos_user_id, core_user_id=core_user_id)

    def map_pos_restaurant(self, *, pos_restaurant_id: Any, core_organization_id: str, core_project_id: str) -> Dict[str, Any]:
        return self.core.map_pos_restaurant(
            pos_restaurant_id=pos_restaurant_id,
            core_organization_id=core_organization_id,
            core_project_id=core_project_id,
        )

    def ensure_pos_membership(self, *, pos_user_id: Any, pos_restaurant_id: Any, core_role: Optional[str] = None) -> Dict[str, Any]:
        core_user_id = self.core.resolve_core_user_for_pos_user(pos_user_id)
        if core_user_id is None:
            raise PermissionDeniedError("POS user is not mapped to a Core user")
        core_org_id = self.core.resolve_core_organization_for_pos_restaurant(pos_restaurant_id)
        if core_org_id is None:
            raise ResourceScopeError("POS restaurant is not mapped to a Core organization")
        membership = self.core._get_organization_membership(core_user_id, core_org_id)
        mapped_role = pos_role_to_core_role(core_role or "viewer")
        if membership is None:
            return self.core.add_organization_membership(user_id=core_user_id, organization_id=core_org_id, role=mapped_role, status="active")
        if membership["status"] != "active":
            raise PermissionDeniedError("Organization membership is inactive")
        return membership

    def ensure_pos_project_scope(self, *, pos_restaurant_id: Any, core_organization_id: Optional[str] = None, core_project_name: Optional[str] = None) -> Dict[str, Any]:
        mapped_org = self.core.resolve_core_organization_for_pos_restaurant(pos_restaurant_id)
        if mapped_org is None:
            raise ResourceScopeError("POS restaurant has no Core organization mapping")
        if core_organization_id is not None and mapped_org != core_organization_id:
            raise ResourceScopeError("POS restaurant is mapped to a different Core organization")
        mapped_project = self.core.resolve_core_project_for_pos_restaurant(pos_restaurant_id)
        if mapped_project is None:
            raise ResourceScopeError("POS restaurant has no Core project mapping")
        project = self.core.get_project(mapped_project)
        if project is None:
            raise ResourceScopeError("Mapped Core project does not exist")
        if project["organization_id"] != mapped_org:
            raise ResourceScopeError("Mapped POS restaurant project does not belong to the mapped organization")
        if core_project_name and project["name"] != core_project_name:
            raise ResourceScopeError("Requested project name does not match the mapped project")
        return project

    def resolve_authenticated_request(
        self,
        *,
        pos_user_id: Any,
        pos_restaurant_id: Any,
        module_key: str = "pos",
        request_id: Optional[str] = None,
        required_permission: Optional[str] = None,
    ) -> Dict[str, Any]:
        request_id = request_id or f"req-pos-{pos_user_id}-{pos_restaurant_id}"
        core_user_id = self.core.resolve_core_user_for_pos_user(pos_user_id)
        if core_user_id is None:
            raise PermissionDeniedError("POS user has no Core identity mapping")

        user = self.core.get_user(core_user_id)
        if user is None or user["status"] != "active":
            raise PermissionDeniedError("Core user is unknown or inactive")

        core_org_id = self.core.resolve_core_organization_for_pos_restaurant(pos_restaurant_id)
        if core_org_id is None:
            raise ResourceScopeError("POS restaurant has no mapped Core organization")

        core_project_id = self.core.resolve_core_project_for_pos_restaurant(pos_restaurant_id)
        if core_project_id is None:
            raise ResourceScopeError("POS restaurant has no mapped Core project")

        project = self.core.get_project(core_project_id)
        if project is None or project["status"] != "active":
            raise PermissionDeniedError("Core project is disabled or missing")
        if project["organization_id"] != core_org_id:
            raise ResourceScopeError("POS restaurant project does not belong to the mapped organization")

        org = self.core.get_organization(core_org_id)
        if org is None or org["status"] != "active":
            raise PermissionDeniedError("Core organization is inactive or missing")

        membership = self.core._get_organization_membership(core_user_id, core_org_id)
        if membership is None or membership["status"] != "active":
            raise PermissionDeniedError("POS user is not active in the mapped Core organization")

        project_membership = self.core._get_project_membership(core_user_id, core_project_id)
        if project_membership is None or project_membership["status"] != "active":
            if _normalize_role(membership["role"]) not in {"platform_admin", "organization_owner", "organization_admin"}:
                raise PermissionDeniedError("POS user does not have project membership in the mapped restaurant project")

        self.core.require_scope(user_id=core_user_id, organization_id=core_org_id, project_id=core_project_id, module_key=module_key)
        permissions = self.core._effective_permissions(user_id=core_user_id, organization_id=core_org_id, project_id=core_project_id)

        if required_permission and required_permission not in permissions:
            raise PermissionDeniedError(f"Missing required permission: {required_permission}")

        target_module = _normalize_module_key(module_key)
        if not self.core.module_access_enabled(organization_id=core_org_id, project_id=core_project_id, module_key=target_module):
            raise PermissionDeniedError(f"Module '{target_module}' is not enabled for this scope")

        return {
            "current_user": core_user_id,
            "current_organization": core_org_id,
            "current_project": core_project_id,
            "current_module": target_module,
            "permissions": permissions,
            "request_id": request_id,
            "user": user,
            "organization": org,
            "project": project,
            "pos_user_id": str(pos_user_id),
            "pos_restaurant_id": str(pos_restaurant_id),
        }


def require_pos_core_scope(module_key: str = "pos", required_permission: Optional[str] = None, *, pos_user_id_provider=None, pos_restaurant_id_provider=None):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                pos_user_id = None
                pos_restaurant_id = None
                if callable(pos_user_id_provider):
                    pos_user_id = pos_user_id_provider()
                elif pos_user_id_provider is not None:
                    pos_user_id = pos_user_id_provider
                else:
                    pos_user_id = getattr(current_user, "id", None)

                if callable(pos_restaurant_id_provider):
                    pos_restaurant_id = pos_restaurant_id_provider()
                elif pos_restaurant_id_provider is not None:
                    pos_restaurant_id = pos_restaurant_id_provider
                else:
                    pos_restaurant_id = getattr(current_user, "restaurant_id", None)

                if not pos_user_id or pos_restaurant_id is None:
                    raise PermissionDeniedError("POS authentication and restaurant scope are required")

                adapter = POSCoreAdapter(service=create_core_service())
                ctx = adapter.resolve_authenticated_request(
                    pos_user_id=pos_user_id,
                    pos_restaurant_id=pos_restaurant_id,
                    module_key=module_key,
                    request_id=request.headers.get("X-Request-ID") if hasattr(request, "headers") else None,
                    required_permission=required_permission,
                )
                g.core_context = ctx
                g.current_organization = ctx["current_organization"]
                g.current_project = ctx["current_project"]
                g.current_module = ctx["current_module"]
                g.current_user = ctx["current_user"]
                return func(*args, **kwargs)
            except PermissionDeniedError:
                from flask import abort
                abort(403)
            except ResourceScopeError:
                from flask import abort
                abort(403)

        return wrapped

    return decorator
