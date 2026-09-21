from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import psycopg2


MIGRATIONS_DIR = Path(__file__).resolve().parent


class CoreMigrationRunner:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _files(self) -> List[Tuple[str, Path, Path]]:
        files = []
        for path in sorted(MIGRATIONS_DIR.glob("[0-9]*_*.sql")):
            if path.name.endswith(".down.sql"):
                continue
            down = path.with_name(path.name[:-4] + ".down.sql")
            files.append((path.name.split("_", 1)[0], path, down))
        return files

    def _connect(self):
        return psycopg2.connect(self.database_url)

    def ensure_history(self, connection) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS core_schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def applied(self, *, create_history: bool = True) -> List[str]:
        with self._connect() as connection:
            if create_history:
                self.ensure_history(connection)
            with connection.cursor() as cursor:
                if not create_history:
                    cursor.execute("SELECT to_regclass('public.core_schema_migrations')")
                    if cursor.fetchone()[0] is None:
                        return []
                cursor.execute("SELECT version FROM core_schema_migrations ORDER BY version")
                return [row[0] for row in cursor.fetchall()]

    def status(self, *, create_history: bool = True) -> dict:
        applied = self.applied(create_history=create_history)
        versions = [version for version, _, _ in self._files()]
        return {"applied": applied, "pending": [version for version in versions if version not in applied], "head": versions[-1] if versions else None}

    def upgrade(self) -> dict:
        with self._connect() as connection:
            self.ensure_history(connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT version FROM core_schema_migrations")
                applied = {row[0] for row in cursor.fetchall()}
                for version, path, _ in self._files():
                    if version in applied:
                        continue
                    cursor.execute(path.read_text(encoding="ascii"))
                    cursor.execute("INSERT INTO core_schema_migrations (version) VALUES (%s)", (version,))
        return self.status()

    def downgrade(self, version: str) -> dict:
        files = {item[0]: item for item in self._files()}
        if version not in files:
            raise ValueError(f"Unknown Core migration: {version}")
        with self._connect() as connection:
            self.ensure_history(connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT version FROM core_schema_migrations WHERE version = %s", (version,))
                if cursor.fetchone() is None:
                    return self.status()
                cursor.execute(files[version][2].read_text(encoding="ascii"))
                cursor.execute("DELETE FROM core_schema_migrations WHERE version = %s", (version,))
        return self.status()