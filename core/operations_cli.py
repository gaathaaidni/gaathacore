from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import psycopg2

from core.config import core_database_url
from core.migrations.runner import CoreMigrationRunner
from core.operations import core_health


def _url() -> str:
    return core_database_url()


def _identity(database_url: str) -> dict[str, Any]:
    with psycopg2.connect(database_url, connect_timeout=3) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, current_setting('server_version')")
            database, user, version = cursor.fetchone()
    return {"database": database, "user": user, "server_version": version}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GaathaCore staging operations")
    parser.add_argument("command", choices=("status", "upgrade", "health", "identity"))
    args = parser.parse_args(argv)
    try:
        if args.command == "health":
            result = core_health()
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "ready" else 1
        database_url = _url()
        if args.command == "identity":
            print(json.dumps(_identity(database_url), sort_keys=True))
            return 0
        runner = CoreMigrationRunner(database_url)
        result = runner.upgrade() if args.command == "upgrade" else runner.status(create_history=False)
        print(json.dumps(result, sort_keys=True))
        return 0 if not result["pending"] else 1
    except psycopg2.Error as exc:
        print(f"Core staging operation failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Core staging operation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
