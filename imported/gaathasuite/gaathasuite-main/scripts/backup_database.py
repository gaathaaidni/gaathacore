#!/usr/bin/env python3
"""Create a safe PostgreSQL dump and verify it without altering the live database."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def log_event(message: str, log_path: Path | None = None) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{timestamp}] {message}"
    print(line)
    if log_path is not None:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{line}\n")
        except OSError:
            pass


def resolve_database_settings(database_url: str | None = None) -> dict:
    database_url = database_url or os.environ.get("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        if not parsed.scheme.startswith("postgresql"):
            raise ValueError("DATABASE_URL must use a PostgreSQL scheme")
        db_user = parsed.username or os.environ.get("POSTGRES_USER")
        db_password = parsed.password or os.environ.get("POSTGRES_PASSWORD")
        db_host = parsed.hostname or os.environ.get("DATABASE_HOST", "localhost")
        db_port = parsed.port or int(os.environ.get("DATABASE_PORT", "5432"))
        db_name = parsed.path.lstrip("/") or os.environ.get("POSTGRES_DB")
    else:
        db_user = os.environ.get("POSTGRES_USER")
        db_password = os.environ.get("POSTGRES_PASSWORD")
        db_host = os.environ.get("DATABASE_HOST", "localhost")
        db_port = int(os.environ.get("DATABASE_PORT", "5432"))
        db_name = os.environ.get("POSTGRES_DB")

    if not db_user or not db_name:
        raise ValueError(
            "A PostgreSQL backup requires POSTGRES_USER and POSTGRES_DB or a DATABASE_URL."
        )

    return {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_password,
        "database": db_name,
    }


def verify_command_available(command: str) -> str:
    resolved = shutil.which(command)
    if not resolved:
        raise RuntimeError(f"Required command '{command}' was not found in PATH.")
    return resolved


def run_command(command: list[str], *, env: dict | None = None, log_path: Path | None = None) -> subprocess.CompletedProcess:
    log_event(f"Running: {' '.join(command)}", log_path)
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    if result.stdout:
        log_event(result.stdout.strip(), log_path)
    if result.stderr:
        log_event(result.stderr.strip(), log_path)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr.strip()}"
        )
    return result


def verify_backup_archive(dump_path: Path) -> None:
    if not dump_path.exists() or dump_path.stat().st_size == 0:
        raise RuntimeError(f"Backup archive is missing or empty: {dump_path}")
    result = subprocess.run(
        ["pg_restore", "--list", str(dump_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Backup archive failed verification: {result.stderr.strip()}")
    if not result.stdout.strip():
        raise RuntimeError(f"Backup archive did not contain any restoreable entries: {dump_path}")


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> None:
    if retention_days <= 0:
        return
    cutoff = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
    for path in backup_dir.glob("*.dump"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            log_event(f"Removed expired backup archive: {path}", backup_dir / "backup.log")


def build_dump_path(backup_dir: Path, database_name: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return backup_dir / f"{database_name}-{timestamp}.dump"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a verified PostgreSQL backup archive.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="PostgreSQL URL to back up")
    parser.add_argument("--backup-dir", default=os.environ.get("BACKUP_DIR", "/var/backups/gaathasuite"), help="Directory for backup archives")
    parser.add_argument("--retention-days", type=int, default=int(os.environ.get("BACKUP_RETENTION_DAYS", "30")), help="Delete archives older than this many days")
    return parser.parse_known_args()[0]


def main() -> int:
    args = parse_args()
    backup_dir = Path(args.backup_dir)
    log_path = backup_dir / "backup.log"
    try:
        settings = resolve_database_settings(args.database_url)
        verify_command_available("pg_dump")
        verify_command_available("pg_restore")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path.cwd() / "backups"
            log_event(
                f"Permission denied for {backup_dir}; falling back to {fallback}",
                log_path,
            )
            backup_dir = fallback
            backup_dir.mkdir(parents=True, exist_ok=True)

        dump_path = build_dump_path(backup_dir, settings["database"])
        env = os.environ.copy()
        if settings["password"]:
            env["PGPASSWORD"] = settings["password"]

        pg_dump_cmd = [
            "pg_dump",
            "-h",
            settings["host"],
            "-p",
            str(settings["port"]),
            "-U",
            settings["user"],
            "-d",
            settings["database"],
            "--format=custom",
            "--file",
            str(dump_path),
        ]
        run_command(pg_dump_cmd, env=env, log_path=log_path)
        verify_backup_archive(dump_path)
        cleanup_old_backups(backup_dir, args.retention_days)
        log_event(f"Backup completed successfully: {dump_path}", log_path)
        print(f"OK: verified PostgreSQL backup saved to {dump_path}")
        return 0
    except Exception as exc:  # pragma: no cover - exercised by tests through monkeypatching
        message = f"ERROR: {exc}"
        log_event(message, log_path)
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
