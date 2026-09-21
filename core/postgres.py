from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor

from core.migrations.runner import CoreMigrationRunner
from core.platform import GaathaCoreService, ResourceScopeError, _json_default, _normalize_module_key, _utcnow


class _PostgresConnection:
    def __init__(self, raw_connection):
        self.raw_connection = raw_connection

    def __enter__(self):
        self.raw_connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self.raw_connection.__exit__(exc_type, exc_value, traceback)
        finally:
            self.raw_connection.close()

    def execute(self, query: str, params=()):
        query = query.replace("?", "%s")
        try:
            cursor = self.raw_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            return cursor
        except IntegrityError as exc:
            self.raw_connection.rollback()
            raise __import__("sqlite3").IntegrityError(str(exc)) from exc


class PostgresCoreService(GaathaCoreService):
    """PostgreSQL implementation of the Phase 4 Core service API.

    Product credentials and product records remain outside this database. The
    inherited service methods are kept as the compatibility surface for the
    adapters while SQL execution is redirected to PostgreSQL.
    """

    def __init__(self, database_url: str, *, migrate: bool = True) -> None:
        self.database_url = database_url
        if migrate:
            CoreMigrationRunner(database_url).upgrade()

    def _connect(self) -> _PostgresConnection:
        return _PostgresConnection(psycopg2.connect(self.database_url))

    def _get_memberships(self, query: str, params) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = self._fetch_all(connection, query, params)
            return [self._row_to_dict(row) for row in rows]

    def get_organization_memberships(self, organization_id: str) -> List[Dict[str, Any]]:
        return self._get_memberships(
            "SELECT * FROM organization_memberships WHERE organization_id = ? ORDER BY created_at ASC, id ASC",
            (organization_id,),
        )

    def get_project_memberships(self, project_id: str) -> List[Dict[str, Any]]:
        return self._get_memberships(
            "SELECT * FROM project_memberships WHERE project_id = ? ORDER BY created_at ASC, id ASC",
            (project_id,),
        )

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
        with self._connect() as connection:
            if project_id is None:
                row = self._fetch_one(connection, "SELECT * FROM module_access WHERE organization_id = ? AND project_id IS NULL AND module_key = ?", (organization_id, module))
            else:
                row = self._fetch_one(connection, "SELECT * FROM module_access WHERE organization_id = ? AND project_id = ? AND module_key = ?", (organization_id, project_id, module))
            now = _utcnow()
            payload = json.dumps(configuration or {}, default=_json_default)
            if row is None:
                record_id = self._uuid()
                connection.execute(
                    "INSERT INTO module_access (id, organization_id, project_id, module_key, enabled, status, configuration, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?::jsonb, ?, ?)",
                    (record_id, organization_id, project_id, module, enabled, "enabled" if enabled else "disabled", payload, now, now),
                )
                row = self._fetch_one(connection, "SELECT * FROM module_access WHERE id = ?", (record_id,))
            else:
                connection.execute(
                    "UPDATE module_access SET enabled = ?, status = ?, configuration = ?::jsonb, updated_at = ? WHERE id = ?",
                    (enabled, "enabled" if enabled else "disabled", payload, now, row["id"]),
                )
                row = self._fetch_one(connection, "SELECT * FROM module_access WHERE id = ?", (row["id"],))
            return self._row_to_dict(row)

    def log_audit(self, **kwargs) -> Dict[str, Any]:
        event_id = self._uuid()
        now = _utcnow()
        organization_id = kwargs.get("organization_id")
        project_id = kwargs.get("project_id")
        if kwargs.get("user_id") is not None and self.get_user(kwargs["user_id"]) is None:
            raise ResourceScopeError("Audit actor does not exist")
        if organization_id is not None and self.get_organization(organization_id) is None:
            raise ResourceScopeError("Audit organization does not exist")
        if project_id is not None:
            project = self.get_project(project_id)
            if project is None or project["organization_id"] != organization_id:
                raise ResourceScopeError("Audit project does not match the organization")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO audit_events (id, timestamp, user_id, organization_id, project_id, module, action, resource_type, resource_id, success, correlation_id, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?)",
                (
                    event_id, now, kwargs.get("user_id"), organization_id, project_id,
                    _normalize_module_key(kwargs.get("module_key")), kwargs["action"], kwargs.get("resource_type"),
                    kwargs.get("resource_id"), kwargs.get("success", True), kwargs.get("correlation_id"),
                    json.dumps(kwargs.get("metadata") or {}, default=_json_default), now,
                ),
            )
            row = self._fetch_one(connection, "SELECT * FROM audit_events WHERE id = ?", (event_id,))
            return self._row_to_dict(row)

    def record_usage(self, **kwargs) -> Dict[str, Any]:
        self.require_scope(
            user_id=kwargs["user_id"], organization_id=kwargs["organization_id"],
            project_id=kwargs.get("project_id"), module_key=kwargs["module_key"],
        )
        usage_id = self._uuid()
        now = _utcnow()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO usage_events (id, event_timestamp, user_id, organization_id, project_id, module_key, feature, source_service, quantity, unit, idempotency_key, correlation_id, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?)",
                (
                    usage_id, now, kwargs["user_id"], kwargs["organization_id"], kwargs.get("project_id"),
                    _normalize_module_key(kwargs["module_key"]), kwargs["feature"], kwargs["source_service"],
                    float(kwargs["quantity"]), kwargs["unit"], kwargs.get("idempotency_key"), kwargs.get("correlation_id"),
                    json.dumps(kwargs.get("metadata") or {}, default=_json_default), now,
                ),
            )
            row = self._fetch_one(connection, "SELECT * FROM usage_events WHERE id = ?", (usage_id,))
            return self._row_to_dict(row)