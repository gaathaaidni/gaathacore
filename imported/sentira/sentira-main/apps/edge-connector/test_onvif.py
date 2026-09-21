import asyncio
from xml.etree import ElementTree as ET

import pytest

from command_executor import execute_onvif_operation
from onvif.auth import PASSWORD_DIGEST, password_digest, username_token
from onvif.client import OnvifClient
from onvif.exceptions import OnvifError
from onvif.fixtures import DEVICE_INFORMATION_RESPONSE, PROFILES_RESPONSE, SERVICES_RESPONSE, SOAP_FAULT_RESPONSE, STREAM_URI_RESPONSE


class FixtureTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    async def post(self, url, body, timeout, username="", password=""):
        self.requests.append((url, body, username, password))
        operation = next(element for element in ET.fromstring(body).iter() if element.tag.endswith("GetServices") or element.tag.endswith("GetDeviceInformation") or element.tag.endswith("GetProfiles") or element.tag.endswith("GetStreamUri"))
        name = operation.tag.rsplit("}", 1)[-1]
        expected = {"GetServices": SERVICES_RESPONSE, "GetDeviceInformation": DEVICE_INFORMATION_RESPONSE, "GetProfiles": PROFILES_RESPONSE, "GetStreamUri": STREAM_URI_RESPONSE}[name]
        response = self.responses.pop(0) if self.responses else expected
        return response


@pytest.mark.asyncio
async def test_onvif_operations_parse_fixtures_and_redact_uri():
    transport = FixtureTransport([])
    client = OnvifClient("http://192.0.2.10/onvif/device_service", transport=transport)
    assert await client.get_device_information() == {"manufacturer": "ExampleCam", "model": "XC-200", "firmware": "1.2.3", "serialNumber": "SN-42", "hardwareId": "HW-7"}
    profiles = await client.get_profiles()
    assert profiles[0].token == "main"
    assert profiles[0].resolution == {"width": 1920, "height": 1080}
    stream = await client.get_stream_uri("main")
    assert stream["uri"] == "rtsp://192.0.2.10:554/live"
    assert "password" not in str(stream)
    assert all(ET.fromstring(request[1]).find("{http://www.w3.org/2003/05/soap-envelope}Body") is not None for request in transport.requests)


def test_ws_security_digest_is_deterministic_and_not_plaintext():
    assert password_digest(b"nonce", "2026-01-01T00:00:00Z", "secret")
    token = username_token("admin", "secret")
    assert PASSWORD_DIGEST.encode() in token
    assert b"secret" not in token


@pytest.mark.asyncio
async def test_onvif_soap_fault_is_structured():
    transport = FixtureTransport([SOAP_FAULT_RESPONSE])
    client = OnvifClient("http://192.0.2.10/onvif/device_service", transport=transport)
    with pytest.raises(OnvifError) as error:
        await client.get_device_information()
    assert error.value.code == "ONVIF_SOAP_FAULT"


@pytest.mark.asyncio
async def test_command_executor_returns_real_device_information(monkeypatch):
    transport = FixtureTransport([])
    monkeypatch.setattr("command_executor.OnvifClient", lambda *args, **kwargs: OnvifClient(*args, transport=transport, **kwargs))
    result = await execute_onvif_operation({"commandType": "GET_ONVIF_DEVICE_INFORMATION", "payload": {"xaddr": "http://192.0.2.10/onvif/device_service"}}, 10)
    assert result["status"] == "SUCCEEDED"
    assert result["result"]["device"]["manufacturer"] == "ExampleCam"


@pytest.mark.asyncio
async def test_invalid_endpoint_does_not_make_network_request():
    with pytest.raises(OnvifError) as error:
        OnvifClient("rtsp://192.0.2.10/live")
    assert error.value.code == "ONVIF_SERVICE_UNAVAILABLE"
