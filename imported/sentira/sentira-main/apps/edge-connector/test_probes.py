import asyncio

import pytest

from probes import network_addresses, redact_url, rtsp_verify


def test_redact_url_removes_credentials():
    assert redact_url("rtsp://admin:secret@192.168.1.20:554/live") == "rtsp://192.168.1.20:554/live"


def test_discovery_network_is_bounded():
    with pytest.raises(ValueError, match="DISCOVERY_LIMIT_REACHED"):
        network_addresses("192.168.0.0/16", 256)
    assert len(network_addresses("192.168.1.0/30", 256)) == 2


@pytest.mark.asyncio
async def test_rtsp_verification_parses_successful_options(monkeypatch):
    class Reader:
        async def readuntil(self, _separator):
            return b"RTSP/1.0 200 OK\r\nCSeq: 1\r\n\r\n"

    class Writer:
        def write(self, _data):
            pass

        async def drain(self):
            pass

        def close(self):
            pass

        async def wait_closed(self):
            pass

    monkeypatch.setattr("probes.validate_endpoint", lambda _host: "192.168.1.20")
    monkeypatch.setattr("asyncio.open_connection", lambda *_args, **_kwargs: asyncio.sleep(0, result=(Reader(), Writer())))
    result = await rtsp_verify("rtsp://192.168.1.20/live", username="admin", password="secret")
    assert result["status"] == "VERIFIED_CONNECTED"
    assert "secret" not in str(result)


@pytest.mark.asyncio
async def test_rtsp_verification_rejects_embedded_credentials():
    result = await rtsp_verify("rtsp://admin:secret@192.168.1.20/live")
    assert result["status"] == "FAILED"
    assert result["failureCode"] == "RTSP_INVALID_RESPONSE"