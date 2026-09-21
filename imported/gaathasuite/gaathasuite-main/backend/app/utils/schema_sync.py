import importlib
import pkgutil

from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

import app.models
from app.db import Base


def _sql_literal(value) -> str:
    """Render a Python default value into a safe SQL literal for ALTER TABLE."""
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, (int, float)):
        return str(value)
    try:
        return str(value.compile(dialect=postgresql.dialect()))
    except Exception:
        return str(value)


def ensure_schema_compatibility(engine) -> None:
    """Add missing columns required by current SQLAlchemy models to existing tables."""
    # Load all model modules into the current process so Base.metadata includes
    # legacy tables such as department, employee, and other runtime models.
    for _, module_name, _ in pkgutil.walk_packages(app.models.__path__, prefix=app.models.__name__ + '.'):
        try:
            importlib.import_module(module_name)
        except Exception:
            # Best-effort import so schema compatibility still runs even if one
            # model module has an import-time issue.
            continue

    insp = inspect(engine)

    for table_name, table in Base.metadata.tables.items():
        if not insp.has_table(table_name):
            continue

        existing = {column['name'] for column in insp.get_columns(table_name)}

        for column in table.columns:
            if column.name in existing:
                continue

            ddl = (
                f'ALTER TABLE "{table_name}" '
                f'ADD COLUMN "{column.name}" {column.type.compile(dialect=postgresql.dialect())}'
            )

            if column.nullable is False:
                ddl += ' NOT NULL'

            # Skip default expressions for compatibility DDL. Existing databases
            # may contain legacy defaults or non-portable expressions that cannot
            # be re-emitted safely during ALTER TABLE.
            if False:
                default_sql = None
                if column.server_default is not None:
                    default_sql = str(column.server_default.arg)
                elif column.default is not None:
                    default_value = column.default.arg if hasattr(column.default, 'arg') else column.default
                    default_sql = _sql_literal(default_value)

                if default_sql:
                    ddl += f' DEFAULT {default_sql}'

            with engine.begin() as conn:
                conn.execute(text(ddl))
