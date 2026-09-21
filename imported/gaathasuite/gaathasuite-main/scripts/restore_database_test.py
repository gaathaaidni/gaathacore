#!/usr/bin/env python3
"""Run a PostgreSQL restore rehearsal against a disposable database only."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backup_database import resolve_database_settings, run_command, verify_command_available, verify_backup_archive


def build_restore_name(database_name: str, requested_name: str | None = None) -> str:
    if requested_name:
        restore_name = requested_name
    else:
        restore_name = f"{database_name}_restore_test_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    if restore_name == database_name:
        raise ValueError(
            "Refusing to restore into the live production database. "
            "Use a disposable name such as <database>_restore_test_<timestamp>."
        )
    return restore_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore a PostgreSQL dump to a disposable database for verification.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="Source database URL")
    parser.add_argument("--dump-path", required=True, help="Path to the custom-format dump archive")
    parser.add_argument("--restore-db-name", default=None, help="Disposable target database name")
    parser.add_argument("--log-file", default=None, help="Optional log file for restore operations")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    log_file = Path(args.log_file) if args.log_file else None
    try:
        source_settings = resolve_database_settings(args.database_url)
        dump_path = Path(args.dump_path)
        verify_command_available("createdb")
        verify_command_available("pg_restore")
        verify_command_available("psql")
        verify_backup_archive(dump_path)

        restore_db_name = build_restore_name(source_settings["database"], args.restore_db_name)
        env = os.environ.copy()
        if source_settings["password"]:
            env["PGPASSWORD"] = source_settings["password"]

        createdb_cmd = [
            "createdb",
            "-h",
            source_settings["host"],
            "-p",
            str(source_settings["port"]),
            "-U",
            source_settings["user"],
            restore_db_name,
        ]
        run_command(createdb_cmd, env=env, log_path=log_file)

        pg_restore_cmd = [
            "pg_restore",
            "--exit-on-error",
            "--clean",
            "--if-exists",
            "-h",
            source_settings["host"],
            "-p",
            str(source_settings["port"]),
            "-U",
            source_settings["user"],
            "-d",
            restore_db_name,
            str(dump_path),
        ]
        run_command(pg_restore_cmd, env=env, log_path=log_file)

        validate_cmd = [
            "psql",
            "-h",
            source_settings["host"],
            "-p",
            str(source_settings["port"]),
            "-U",
            source_settings["user"],
            "-d",
            restore_db_name,
            "-At",
            "-c",
            "SELECT 1;",
        ]
        run_command(validate_cmd, env=env, log_path=log_file)

        print(f"OK: restore rehearsal succeeded for disposable database: {restore_db_name}")
        return 0
    except Exception as exc:
        message = f"ERROR: {exc}"
        if log_file is not None:
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                with log_file.open("a", encoding="utf-8") as handle:
                    handle.write(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {message}\n")
            except OSError:
                pass
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
