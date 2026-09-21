from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple


class CoreError(Exception):
    pass


class PermissionDeniedError(CoreError, PermissionError):
    pass


class ResourceScopeError(CoreError):
    pass


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _normalize_role(role: Optional[str]) -> str:
    if role is None:
        return "viewer"
    value = str(role).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "superadmin": "platform_admin",
        "super_admin": "platform_admin",
        "orgadmin": "organization_admin",
        "org_admin": "organization_admin",
        "organizationowner": "organization_owner",
        "organization_owner": "organization_owner",
        "projectadmin": "project_admin",
        "project_admin": "project_admin",
        "restaurantadmin": "organization_admin",
        "restaurant_admin": "organization_admin",
        "staffmember": "staff",
        "member": "viewer",
        "admin": "organization_admin",
    }
    return aliases.get(value, value)


def _normalize_module_key(module_key: Optional[str]) -> str:
    if module_key is None:
        return "suite"
    value = str(module_key).strip().lower().replace("-", "_")
    aliases = {
        "business_suite": "suite",
        "suite": "suite",
        "businesssuite": "suite",
        "pos": "pos",
        "sentira": "sentira",
        "postpilot": "postpilot",
        "post_pilot": "postpilot",
    }
    return aliases.get(value, value)


ROLE_PERMISSIONS: Dict[str, set[str]] = {
    "platform_admin": {
        "organization.read",
        "organization.update",
        "organization.members.manage",
        "project.read",
        "project.update",
        "project.members.manage",
        "module.read",
        "module.manage",
        "audit.read",
        "usage.read",
        "billing.read",
        "billing.manage",
    },
    "organization_owner": {
        "organization.read",
        "organization.update",
        "organization.members.manage",
        "project.read",
        "project.update",
        "project.members.manage",
        "module.read",
        "module.manage",
        "audit.read",
        "usage.read",
        "billing.read",
    },
    "organization_admin": {
        "organization.read",
        "organization.update",
        "project.read",
        "project.update",
        "project.members.manage",
        "module.read",
        "module.manage",
        "audit.read",
        "usage.read",
    },
    "project_admin": {
        "project.read",
        "project.update",
        "project.members.manage",
        "module.read",
        "module.manage",
        "usage.read",
    },
    "manager": {
        "project.read",
        "module.read",
        "usage.read",
    },
    "staff": {
        "project.read",
        "module.read",
    },
    "viewer": {
        "organization.read",
        "project.read",
        "module.read",
        "usage.read",
    },
}


@dataclass
class CoreContext:
    current_user: Optional[str] = None
    current_organization: Optional[str] = None
    current_project: Optional[str] = None
    current_module: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    available_modules: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def module(self) -> Optional[str]:
        return self.current_module


def _json_default(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        return list(value)
    return str(value)


class GaathaCoreService:
    def __init__(self, database_path: str = "gaathacore.db") -> None:
        self.database_path = database_path
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS organization_memberships (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, organization_id)
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(organization_id, slug)
                );

                CREATE TABLE IF NOT EXISTS project_memberships (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(project_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS module_access (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    project_id TEXT,
                    module_key TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'disabled',
                    configuration TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(organization_id, project_id, module_key)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    organization_id TEXT,
                    project_id TEXT,
                    module TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    success INTEGER NOT NULL DEFAULT 1,
                    correlation_id TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS usage_events (
                    id TEXT PRIMARY KEY,
                    event_timestamp TEXT NOT NULL,
                    user_id TEXT,
                    organization_id TEXT,
                    project_id TEXT,
                    module_key TEXT,
                    feature TEXT,
                    source_service TEXT,
                    quantity REAL NOT NULL DEFAULT 0,
                    unit TEXT NOT NULL,
                    idempotency_key TEXT,
                    correlation_id TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS suite_user_map (
                    id TEXT PRIMARY KEY,
                    suite_user_id TEXT NOT NULL UNIQUE,
                    core_user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS suite_organization_map (
                    id TEXT PRIMARY KEY,
                    suite_organization_id TEXT NOT NULL UNIQUE,
                    core_organization_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS suite_project_map (
                    id TEXT PRIMARY KEY,
                    suite_organization_id TEXT NOT NULL,
                    suite_project_id TEXT NOT NULL,
                    core_project_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(suite_organization_id, suite_project_id)
                );

                CREATE TABLE IF NOT EXISTS pos_user_map (
                    id TEXT PRIMARY KEY,
                    pos_user_id TEXT NOT NULL UNIQUE,
                    core_user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pos_restaurant_map (
                    id TEXT PRIMARY KEY,
                    pos_restaurant_id TEXT NOT NULL UNIQUE,
                    core_organization_id TEXT NOT NULL,
                    core_project_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(usage_events)").fetchall()}
            if "event_timestamp" not in columns:
                connection.execute("ALTER TABLE usage_events ADD COLUMN event_timestamp TEXT")
                connection.execute("UPDATE usage_events SET event_timestamp = created_at WHERE event_timestamp IS NULL")
            if "idempotency_key" not in columns:
                connection.execute("ALTER TABLE usage_events ADD COLUMN idempotency_key TEXT")
            if "metadata" not in columns:
                connection.execute("ALTER TABLE usage_events ADD COLUMN metadata TEXT")

    def _uuid(self) -> str:
        return str(uuid.uuid4())

    def _fetch_one(self, connection: sqlite3.Connection, query: str, params: Sequence[Any]) -> Optional[sqlite3.Row]:
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return row

    def _fetch_all(self, connection: sqlite3.Connection, query: str, params: Sequence[Any]) -> List[sqlite3.Row]:
        cursor = connection.execute(query, params)
        return cursor.fetchall()

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}

    def role_permissions(self, role: str) -> List[str]:
        normalized = _normalize_role(role)
        permissions = set(ROLE_PERMISSIONS.get(normalized, set()))
        if normalized == "platform_admin":
            permissions.update({"organization.read", "organization.update", "organization.members.manage", "project.read", "project.update", "project.members.manage", "module.read", "module.manage", "audit.read", "usage.read", "billing.read", "billing.manage"})
        return sorted(permissions)

    def create_user(
        self,
        *,
        email: str,
        username: str,
        display_name: Optional[str] = None,
        status: str = "active",
    ) -> Dict[str, Any]:
        email_value = (email or "").strip()
        username_value = (username or "").strip()
        if not email_value or not username_value:
            raise ValueError("email and username are required")
        user_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO users (id, email, username, display_name, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, email_value.lower(), username_value, display_name or username_value, status, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("username or email already exists") from exc
            row = self._fetch_one(connection, "SELECT * FROM users WHERE id = ?", (user_id,))
            return self._row_to_dict(row)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(connection, "SELECT * FROM users WHERE id = ?", (user_id,))
            return self._row_to_dict(row)

    def get_organization(self, organization_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(connection, "SELECT * FROM organizations WHERE id = ?", (organization_id,))
            return self._row_to_dict(row)

    def create_organization(self, *, name: str, slug: str, status: str = "active") -> Dict[str, Any]:
        name_value = (name or "").strip()
        slug_value = (slug or "").strip().lower().replace(" ", "-")
        if not name_value or not slug_value:
            raise ValueError("name and slug are required")
        org_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO organizations (id, name, slug, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (org_id, name_value, slug_value, status, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("organization slug already exists") from exc
            row = self._fetch_one(connection, "SELECT * FROM organizations WHERE id = ?", (org_id,))
            return self._row_to_dict(row)

    def add_organization_membership(
        self,
        *,
        user_id: str,
        organization_id: str,
        role: str,
        status: str = "active",
    ) -> Dict[str, Any]:
        if not self.get_user(user_id):
            raise PermissionDeniedError("Unknown user")
        if not self.get_organization(organization_id):
            raise ResourceScopeError("Unknown organization")
        normalized_role = _normalize_role(role)
        membership_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT * FROM organization_memberships WHERE user_id = ? AND organization_id = ?",
                (user_id, organization_id),
            )
            if row is not None:
                connection.execute(
                    "UPDATE organization_memberships SET role = ?, status = ?, updated_at = ? WHERE user_id = ? AND organization_id = ?",
                    (normalized_role, status, now, user_id, organization_id),
                )
                row = self._fetch_one(connection, "SELECT * FROM organization_memberships WHERE user_id = ? AND organization_id = ?", (user_id, organization_id))
                return self._row_to_dict(row)
            connection.execute(
                "INSERT INTO organization_memberships (id, user_id, organization_id, role, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (membership_id, user_id, organization_id, normalized_role, status, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM organization_memberships WHERE id = ?", (membership_id,))
            return self._row_to_dict(row)

    def get_organization_memberships(self, organization_id: str) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = self._fetch_all(connection, "SELECT * FROM organization_memberships WHERE organization_id = ? ORDER BY created_at ASC, rowid ASC", (organization_id,))
            return [self._row_to_dict(row) for row in rows]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(connection, "SELECT * FROM projects WHERE id = ?", (project_id,))
            return self._row_to_dict(row)

    def get_project_by_slug(self, organization_id: str, slug: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT * FROM projects WHERE organization_id = ? AND slug = ?",
                (organization_id, str(slug).strip().lower().replace(" ", "-")),
            )
            return self._row_to_dict(row)

    def get_organization_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(connection, "SELECT * FROM organizations WHERE slug = ?", (slug,))
            return self._row_to_dict(row)

    def create_project(
        self,
        *,
        organization_id: str,
        name: str,
        slug: str,
        project_type: str,
        status: str = "active",
    ) -> Dict[str, Any]:
        org = self.get_organization(organization_id)
        if org is None:
            raise ResourceScopeError("Organization does not exist")
        project_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO projects (id, organization_id, name, slug, project_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (project_id, organization_id, name.strip(), slug.strip().lower().replace(" ", "-"), project_type.strip(), status, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("project slug already exists for that organization") from exc
            row = self._fetch_one(connection, "SELECT * FROM projects WHERE id = ?", (project_id,))
            return self._row_to_dict(row)

    def add_project_membership(
        self,
        *,
        project_id: str,
        user_id: str,
        role: str,
        status: str = "active",
    ) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if project is None:
            raise ResourceScopeError("Project does not exist")
        if not self.get_user(user_id):
            raise PermissionDeniedError("Unknown user")
        normalized_role = _normalize_role(role)
        membership_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT * FROM project_memberships WHERE project_id = ? AND user_id = ?",
                (project_id, user_id),
            )
            if row is not None:
                connection.execute(
                    "UPDATE project_memberships SET role = ?, status = ?, updated_at = ? WHERE project_id = ? AND user_id = ?",
                    (normalized_role, status, now, project_id, user_id),
                )
                row = self._fetch_one(connection, "SELECT * FROM project_memberships WHERE project_id = ? AND user_id = ?", (project_id, user_id))
                return self._row_to_dict(row)
            connection.execute(
                "INSERT INTO project_memberships (id, project_id, user_id, role, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (membership_id, project_id, user_id, normalized_role, status, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM project_memberships WHERE id = ?", (membership_id,))
            return self._row_to_dict(row)

    def get_project_memberships(self, project_id: str) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = self._fetch_all(connection, "SELECT * FROM project_memberships WHERE project_id = ? ORDER BY created_at ASC, rowid ASC", (project_id,))
            return [self._row_to_dict(row) for row in rows]

    def map_suite_user(self, *, suite_user_id: Any, core_user_id: str) -> Dict[str, Any]:
        normalized_suite_user_id = str(suite_user_id)
        user = self.get_user(core_user_id)
        if user is None:
            raise PermissionDeniedError("Core user does not exist")
        now = _utcnow()
        with self._connect() as connection:
            existing = self._fetch_one(
                connection,
                "SELECT * FROM suite_user_map WHERE suite_user_id = ?",
                (normalized_suite_user_id,),
            )
            if existing is not None:
                if existing["core_user_id"] != core_user_id:
                    raise ResourceScopeError("Suite user already mapped to a different Core user")
                return self._row_to_dict(existing)
            mapping_id = self._uuid()
            connection.execute(
                "INSERT INTO suite_user_map (id, suite_user_id, core_user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (mapping_id, normalized_suite_user_id, core_user_id, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM suite_user_map WHERE id = ?", (mapping_id,))
            return self._row_to_dict(row)

    def resolve_core_user_for_suite_user(self, suite_user_id: Any) -> Optional[str]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT core_user_id FROM suite_user_map WHERE suite_user_id = ?",
                (str(suite_user_id),),
            )
            return row["core_user_id"] if row else None

    def map_suite_organization(self, *, suite_organization_id: Any, core_organization_id: str) -> Dict[str, Any]:
        normalized_suite_organization_id = str(suite_organization_id)
        org = self.get_organization(core_organization_id)
        if org is None:
            raise ResourceScopeError("Core organization does not exist")
        now = _utcnow()
        with self._connect() as connection:
            existing = self._fetch_one(
                connection,
                "SELECT * FROM suite_organization_map WHERE suite_organization_id = ?",
                (normalized_suite_organization_id,),
            )
            if existing is not None:
                if existing["core_organization_id"] != core_organization_id:
                    raise ResourceScopeError("Suite organization already mapped to a different Core organization")
                return self._row_to_dict(existing)
            mapping_id = self._uuid()
            connection.execute(
                "INSERT INTO suite_organization_map (id, suite_organization_id, core_organization_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (mapping_id, normalized_suite_organization_id, core_organization_id, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM suite_organization_map WHERE id = ?", (mapping_id,))
            return self._row_to_dict(row)

    def resolve_core_organization_for_suite_organization(self, suite_organization_id: Any) -> Optional[str]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT core_organization_id FROM suite_organization_map WHERE suite_organization_id = ?",
                (str(suite_organization_id),),
            )
            return row["core_organization_id"] if row else None

    def map_suite_project(self, *, suite_organization_id: Any, suite_project_id: Any, core_project_id: str) -> Dict[str, Any]:
        project = self.get_project(core_project_id)
        if project is None:
            raise ResourceScopeError("Core project does not exist")
        org = self.get_organization(project["organization_id"])
        if org is None:
            raise ResourceScopeError("Core project is orphaned from an organization")
        if project["organization_id"] != self.resolve_core_organization_for_suite_organization(suite_organization_id):
            raise ResourceScopeError("Suite project does not map to the same Core organization")
        now = _utcnow()
        with self._connect() as connection:
            existing = self._fetch_one(
                connection,
                "SELECT * FROM suite_project_map WHERE suite_organization_id = ? AND suite_project_id = ?",
                (str(suite_organization_id), str(suite_project_id)),
            )
            if existing is not None:
                if existing["core_project_id"] != core_project_id:
                    raise ResourceScopeError("Suite project already mapped to a different Core project")
                return self._row_to_dict(existing)
            mapping_id = self._uuid()
            connection.execute(
                "INSERT INTO suite_project_map (id, suite_organization_id, suite_project_id, core_project_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (mapping_id, str(suite_organization_id), str(suite_project_id), core_project_id, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM suite_project_map WHERE id = ?", (mapping_id,))
            return self._row_to_dict(row)

    def resolve_core_project_for_suite_project(self, *, suite_organization_id: Any, suite_project_id: Any) -> Optional[str]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT core_project_id FROM suite_project_map WHERE suite_organization_id = ? AND suite_project_id = ?",
                (str(suite_organization_id), str(suite_project_id)),
            )
            return row["core_project_id"] if row else None

    def map_pos_user(self, *, pos_user_id: Any, core_user_id: str) -> Dict[str, Any]:
        normalized_pos_user_id = str(pos_user_id)
        user = self.get_user(core_user_id)
        if user is None:
            raise PermissionDeniedError("Core user does not exist")
        now = _utcnow()
        with self._connect() as connection:
            existing = self._fetch_one(
                connection,
                "SELECT * FROM pos_user_map WHERE pos_user_id = ?",
                (normalized_pos_user_id,),
            )
            if existing is not None:
                if existing["core_user_id"] != core_user_id:
                    raise ResourceScopeError("POS user already mapped to a different Core user")
                return self._row_to_dict(existing)
            mapping_id = self._uuid()
            connection.execute(
                "INSERT INTO pos_user_map (id, pos_user_id, core_user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (mapping_id, normalized_pos_user_id, core_user_id, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM pos_user_map WHERE id = ?", (mapping_id,))
            return self._row_to_dict(row)

    def resolve_core_user_for_pos_user(self, pos_user_id: Any) -> Optional[str]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT core_user_id FROM pos_user_map WHERE pos_user_id = ?",
                (str(pos_user_id),),
            )
            return row["core_user_id"] if row else None

    def map_pos_restaurant(self, *, pos_restaurant_id: Any, core_organization_id: str, core_project_id: str) -> Dict[str, Any]:
        normalized_pos_restaurant_id = str(pos_restaurant_id)
        org = self.get_organization(core_organization_id)
        if org is None:
            raise ResourceScopeError("Core organization does not exist")
        project = self.get_project(core_project_id)
        if project is None:
            raise ResourceScopeError("Core project does not exist")
        if project["organization_id"] != core_organization_id:
            raise ResourceScopeError("POS restaurant project does not belong to the mapped organization")
        now = _utcnow()
        with self._connect() as connection:
            existing = self._fetch_one(
                connection,
                "SELECT * FROM pos_restaurant_map WHERE pos_restaurant_id = ?",
                (normalized_pos_restaurant_id,),
            )
            if existing is not None:
                if existing["core_organization_id"] != core_organization_id or existing["core_project_id"] != core_project_id:
                    raise ResourceScopeError("POS restaurant already mapped to a different Core tenant")
                return self._row_to_dict(existing)
            mapping_id = self._uuid()
            connection.execute(
                "INSERT INTO pos_restaurant_map (id, pos_restaurant_id, core_organization_id, core_project_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (mapping_id, normalized_pos_restaurant_id, core_organization_id, core_project_id, now, now),
            )
            row = self._fetch_one(connection, "SELECT * FROM pos_restaurant_map WHERE id = ?", (mapping_id,))
            return self._row_to_dict(row)

    def resolve_core_organization_for_pos_restaurant(self, pos_restaurant_id: Any) -> Optional[str]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT core_organization_id FROM pos_restaurant_map WHERE pos_restaurant_id = ?",
                (str(pos_restaurant_id),),
            )
            return row["core_organization_id"] if row else None

    def resolve_core_project_for_pos_restaurant(self, pos_restaurant_id: Any) -> Optional[str]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT core_project_id FROM pos_restaurant_map WHERE pos_restaurant_id = ?",
                (str(pos_restaurant_id),),
            )
            return row["core_project_id"] if row else None

    def module_access_enabled(self, *, organization_id: str, project_id: Optional[str] = None, module_key: str) -> bool:
        module = _normalize_module_key(module_key)
        with self._connect() as connection:
            rows = self._fetch_all(
                connection,
                "SELECT * FROM module_access WHERE organization_id = ? AND module_key = ? ORDER BY created_at ASC",
                (organization_id, module),
            )
            for row in rows:
                row_project_id = row["project_id"]
                if project_id and row_project_id == project_id and row["enabled"] == 1:
                    return True
                if not row_project_id and row["enabled"] == 1:
                    return True
            return False

    def set_module_access(
        self,
        *,
        organization_id: str,
        project_id: Optional[str],
        module_key: str,
        enabled: bool = True,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        module = _normalize_module_key(module_key)
        if project_id is not None:
            project = self.get_project(project_id)
            if project is None or project["organization_id"] != organization_id:
                raise ResourceScopeError("Project is not in the organization")
        row = None
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT * FROM module_access WHERE organization_id = ? AND project_id IS ? AND module_key = ?",
                (organization_id, project_id, module),
            )
            now = _utcnow()
            if row is None:
                record_id = self._uuid()
                connection.execute(
                    "INSERT INTO module_access (id, organization_id, project_id, module_key, enabled, status, configuration, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (record_id, organization_id, project_id, module, int(bool(enabled)), "enabled" if enabled else "disabled", json.dumps(configuration or {}, default=_json_default), now, now),
                )
                row = self._fetch_one(connection, "SELECT * FROM module_access WHERE id = ?", (record_id,))
            else:
                connection.execute(
                    "UPDATE module_access SET enabled = ?, status = ?, configuration = ?, updated_at = ? WHERE id = ?",
                    (int(bool(enabled)), "enabled" if enabled else "disabled", json.dumps(configuration or {}, default=_json_default), now, row["id"]),
                )
                row = self._fetch_one(connection, "SELECT * FROM module_access WHERE id = ?", (row["id"],))
            return self._row_to_dict(row)

    def _get_organization_membership(self, user_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT * FROM organization_memberships WHERE user_id = ? AND organization_id = ?",
                (user_id, organization_id),
            )
            return self._row_to_dict(row)

    def _get_project_membership(self, user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = self._fetch_one(
                connection,
                "SELECT * FROM project_memberships WHERE user_id = ? AND project_id = ?",
                (user_id, project_id),
            )
            return self._row_to_dict(row)

    def _effective_permissions(self, *, user_id: str, organization_id: str, project_id: Optional[str] = None) -> List[str]:
        user = self.get_user(user_id)
        if user is None:
            raise PermissionDeniedError("Unknown user")
        if user["status"] != "active":
            raise PermissionDeniedError("Disabled user")
        organization = self.get_organization(organization_id)
        if organization is None:
            raise ResourceScopeError("Unknown organization")
        org_membership = self._get_organization_membership(user_id, organization_id)
        if org_membership is None:
            raise ResourceScopeError("User is not a member of the organization")
        if org_membership["status"] != "active":
            raise PermissionDeniedError("Organization membership is disabled")
        permissions = set()
        permissions.update(self.role_permissions(org_membership["role"]))
        if project_id is not None:
            project = self.get_project(project_id)
            if project is None:
                raise ResourceScopeError("Project does not exist")
            if project["organization_id"] != organization_id:
                raise ResourceScopeError("Project does not belong to the organization")
            project_membership = self._get_project_membership(user_id, project_id)
            if project_membership is not None and project_membership["status"] == "active":
                permissions.update(self.role_permissions(project_membership["role"]))
        return sorted(permissions)

    def resolve_identity(self, *, user_id: str, organization_id: Optional[str] = None) -> Dict[str, Any]:
        user = self.get_user(user_id)
        if user is None:
            raise PermissionDeniedError("Unknown user")
        if user["status"] != "active":
            raise PermissionDeniedError("Disabled user")
        response: Dict[str, Any] = {"user": user, "organization": None, "membership": None}
        if organization_id is not None:
            org = self.get_organization(organization_id)
            if org is None:
                raise ResourceScopeError("Unknown organization")
            membership = self._get_organization_membership(user_id, organization_id)
            if membership is None or membership["status"] != "active":
                raise PermissionDeniedError("User is not active in the requested organization")
            response["organization"] = org
            response["membership"] = membership
        return response

    def require_scope(
        self,
        *,
        user_id: str,
        organization_id: str,
        project_id: Optional[str] = None,
        module_key: Optional[str] = None,
    ) -> None:
        user = self.get_user(user_id)
        if user is None:
            raise PermissionDeniedError("Unknown user")
        if user["status"] != "active":
            raise PermissionDeniedError("Disabled user")
        org = self.get_organization(organization_id)
        if org is None:
            raise ResourceScopeError("Unknown organization")
        membership = self._get_organization_membership(user_id, organization_id)
        if membership is None or membership["status"] != "active":
            raise ResourceScopeError("User is not a member of the organization")
        if project_id is not None:
            project = self.get_project(project_id)
            if project is None:
                raise ResourceScopeError("Project does not exist")
            if project["organization_id"] != organization_id:
                raise ResourceScopeError("Project does not belong to the organization")
            if project["status"] != "active":
                raise PermissionDeniedError("Project is disabled")
            project_membership = self._get_project_membership(user_id, project_id)
            if project_membership is None or project_membership["status"] != "active":
                if _normalize_role(membership["role"]) not in {"platform_admin", "organization_owner", "organization_admin"}:
                    raise PermissionDeniedError("User does not have project access")
        if module_key is not None:
            module = _normalize_module_key(module_key)
            if not self.module_access_enabled(organization_id=organization_id, project_id=project_id, module_key=module):
                raise PermissionDeniedError(f"Module '{module}' is not enabled for this scope")

    def resolve_context(
        self,
        *,
        user_id: str,
        organization_id: str,
        project_id: Optional[str] = None,
        module_key: Optional[str] = None,
    ) -> CoreContext:
        self.require_scope(user_id=user_id, organization_id=organization_id, project_id=project_id, module_key=module_key)
        user = self.get_user(user_id)
        org = self.get_organization(organization_id)
        project = self.get_project(project_id) if project_id else None
        permissions = self._effective_permissions(user_id=user_id, organization_id=organization_id, project_id=project_id)
        module = _normalize_module_key(module_key)
        available_modules: List[Dict[str, Any]] = []
        with self._connect() as connection:
            rows = self._fetch_all(
                connection,
                "SELECT * FROM module_access WHERE organization_id = ? ORDER BY created_at ASC",
                (organization_id,),
            )
            for row in rows:
                if row["project_id"] is not None and project_id is not None and row["project_id"] != project_id:
                    continue
                available_modules.append({
                    "module": row["module_key"],
                    "status": "enabled" if row["enabled"] == 1 else "disabled",
                    "project_id": row["project_id"],
                })
        if not available_modules and module_key:
            available_modules.append({"module": module, "status": "disabled", "project_id": project_id})
        return CoreContext(
            current_user=user["id"],
            current_organization=org["id"],
            current_project=project["id"] if project else None,
            current_module=module,
            permissions=permissions,
            available_modules=available_modules,
        )

    def ensure_permission(
        self,
        *,
        user_id: str,
        organization_id: str,
        project_id: Optional[str] = None,
        permission: str,
    ) -> None:
        self.require_scope(user_id=user_id, organization_id=organization_id, project_id=project_id)
        permissions = set(self._effective_permissions(user_id=user_id, organization_id=organization_id, project_id=project_id))
        if permission not in permissions:
            raise PermissionDeniedError(f"Permission '{permission}' is required")

    def log_audit(
        self,
        *,
        user_id: Optional[str],
        organization_id: Optional[str],
        project_id: Optional[str],
        module_key: str,
        action: str,
        resource_type: str,
        resource_id: str,
        success: bool,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event_id = self._uuid()
        now = _utcnow()
        module = _normalize_module_key(module_key)
        payload = metadata or {}
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO audit_events (id, timestamp, user_id, organization_id, project_id, module, action, resource_type, resource_id, success, correlation_id, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, now, user_id, organization_id, project_id, module, action, resource_type, resource_id, int(bool(success)), correlation_id, json.dumps(payload, default=_json_default), now),
            )
            row = self._fetch_one(connection, "SELECT * FROM audit_events WHERE id = ?", (event_id,))
            data = self._row_to_dict(row)
            data["success"] = bool(data["success"])
            return data

    def record_usage(
        self,
        *,
        user_id: str,
        organization_id: str,
        project_id: Optional[str],
        module_key: str,
        feature: str,
        source_service: str,
        quantity: float,
        unit: str,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.require_scope(user_id=user_id, organization_id=organization_id, project_id=project_id, module_key=module_key)
        if project_id is not None:
            project = self.get_project(project_id)
            if project is None or project["organization_id"] != organization_id:
                raise ResourceScopeError("Project does not match the organization")
        usage_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO usage_events (id, event_timestamp, user_id, organization_id, project_id, module_key, feature, source_service, quantity, unit, idempotency_key, correlation_id, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (usage_id, now, user_id, organization_id, project_id, _normalize_module_key(module_key), feature, source_service, float(quantity), unit, idempotency_key, correlation_id, json.dumps(metadata or {}, default=_json_default), now),
            )
            row = self._fetch_one(connection, "SELECT * FROM usage_events WHERE id = ?", (usage_id,))
            return self._row_to_dict(row)

    def api_identity(self, *, user_id: str, organization_id: Optional[str] = None) -> Dict[str, Any]:
        identity = self.resolve_identity(user_id=user_id, organization_id=organization_id)
        data = {
            "user": identity["user"],
            "organization": identity["organization"],
            "membership": identity["membership"],
        }
        return {
            "success": True,
            "data": data,
            "error": None,
            "meta": {"request_id": self._uuid(), "scope": "core"},
        }
