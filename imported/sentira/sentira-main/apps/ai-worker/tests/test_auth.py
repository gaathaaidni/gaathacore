import pytest
from fastapi import HTTPException

from main import require_ingest_auth


def test_worker_ingress_rejects_missing_config(monkeypatch):
    monkeypatch.delenv("AI_WORKER_INGEST_TOKEN", raising=False)

    with pytest.raises(HTTPException) as error:
        require_ingest_auth("token")

    assert error.value.status_code == 401


def test_worker_ingress_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv("AI_WORKER_INGEST_TOKEN", "worker-secret")

    with pytest.raises(HTTPException) as error:
        require_ingest_auth("wrong-secret")

    assert error.value.status_code == 401


def test_worker_ingress_accepts_configured_token(monkeypatch):
    monkeypatch.setenv("AI_WORKER_INGEST_TOKEN", "worker-secret")

    assert require_ingest_auth("worker-secret") is None