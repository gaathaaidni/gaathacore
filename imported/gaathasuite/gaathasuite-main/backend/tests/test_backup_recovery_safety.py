import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "backup_database.py"
RESTORE_SCRIPT = ROOT / "scripts" / "restore_database_test.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_backup_database_requires_production_db_settings(monkeypatch):
    module = load_module("backup_database_module", SCRIPT)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)

    try:
        module.resolve_database_settings()
        raise AssertionError("Expected ValueError for incomplete DB settings")
    except ValueError as exc:
        assert "requires POSTGRES_USER" in str(exc)


def test_backup_database_creates_verified_backup_archive(monkeypatch, tmp_path):
    module = load_module("backup_database_module2", SCRIPT)
    backup_dir = tmp_path / "backups"

    monkeypatch.setenv("POSTGRES_USER", "gaatha")
    monkeypatch.setenv("POSTGRES_DB", "gaatha")
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")

    calls = []

    def fake_which(name):
        return "/usr/bin/" + name

    def fake_run_command(command, *, env=None, log_path=None):
        calls.append(command)
        if command[0] == "pg_dump":
            dump_path = Path(command[-1])
            dump_path.write_bytes(b"archive-data")
            return None
        if command[0] == "pg_restore":
            return type("Result", (), {"stdout": "table data\n", "stderr": "", "returncode": 0})()
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(module.shutil, "which", fake_which)
    monkeypatch.setattr(module, "run_command", fake_run_command)
    monkeypatch.setattr(module, "verify_backup_archive", lambda dump_path: None)

    result = module.main()
    assert result == 0
    assert any(cmd[0] == "pg_dump" for cmd in calls)


def test_restore_rehearsal_refuses_live_database_name(monkeypatch):
    module = load_module("restore_module", RESTORE_SCRIPT)
    monkeypatch.setenv("POSTGRES_USER", "gaatha")
    monkeypatch.setenv("POSTGRES_DB", "gaatha")

    try:
        module.build_restore_name("gaatha", "gaatha")
        raise AssertionError("Expected refusal to restore to live database")
    except ValueError as exc:
        assert "Refusing to restore" in str(exc)
