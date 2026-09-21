import asyncio
import json
import time
from typing import Any
from urllib.parse import urlsplit

from config import settings
from onvif import OnvifClient, OnvifError
from onvif.models import OnvifCredentials
from probes import onvif_discover, redact_url, rtsp_verify


def _sanitize_result(result: Any) -> Any:
    if isinstance(result, dict):
        cleaned = {}
        for key, value in result.items():
            key_lower = str(key).lower()
            if any(token in key_lower for token in ["password", "passwd", "secret", "token", "authorization", "credential", "privatekey", "apikey"]):
                continue
            cleaned[key] = _sanitize_result(value)
        return cleaned
    if isinstance(result, list):
        return [_sanitize_result(item) for item in result]
    return result


def _dedupe_devices(devices: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for device in devices:
        host = str(device.get("localAddress") or device.get("xaddr") or "").strip()
        if host and host not in seen:
            seen.add(host)
            deduped.append(device)
    return deduped


async def execute_onvif_operation(command: dict, timeout: float) -> dict:
    command_type = command.get("commandType")
    payload = command.get("payload") or {}
    if command_type == "PING":
        return {"status": "SUCCEEDED", "result": {"ok": True, "commandType": "PING"}, "errorCode": None, "errorMessage": None}
    if command_type == "GET_CAPABILITIES":
        return {"status": "SUCCEEDED", "result": {"capabilities": {"onvif": True, "rtsp": True, "discovery": True}}, "errorCode": None, "errorMessage": None}
    if command_type == "DISCOVER_ONVIF":
        devices = await asyncio.wait_for(onvif_discover(timeout=min(timeout, settings.onvif_timeout_seconds), max_results=settings.discovery_max_results), timeout)
        return {"status": "SUCCEEDED", "result": {"devices": _dedupe_devices(devices)[: settings.discovery_max_results]}, "errorCode": None, "errorMessage": None}
    if command_type in {"GET_ONVIF_DEVICE_INFORMATION", "GET_ONVIF_MEDIA_PROFILES", "GET_ONVIF_STREAM_URI", "VERIFY_ONVIF_DEVICE"}:
        device = payload.get("device") or {}
        target = str(device.get("xaddr") or device.get("deviceServiceUrl") or payload.get("xaddr") or payload.get("deviceServiceUrl") or "")
        if not target:
            return {"status": "FAILED", "errorCode": "INVALID_DEVICE_ENDPOINT", "errorMessage": "No ONVIF device endpoint was provided."}
        try:
            client = OnvifClient(target, OnvifCredentials(str(payload.get("username") or ""), str(payload.get("password") or ""), bool(payload.get("passwordDigest", True))), timeout=min(timeout, settings.onvif_timeout_seconds), retries=settings.onvif_retry_count, retry_delay=settings.onvif_retry_delay_seconds)
            if command_type == "GET_ONVIF_DEVICE_INFORMATION":
                return {"status": "SUCCEEDED", "result": {"operation": command_type, "device": await client.get_device_information()}, "errorCode": None, "errorMessage": None}
            profiles = await client.get_profiles()
            profile_results = [{"token": item.token, "name": item.name, "resolution": item.resolution, "encoding": item.encoding, "fps": item.fps, "videoSource": item.video_source, "videoEncoder": item.video_encoder} for item in profiles]
            if command_type == "GET_ONVIF_MEDIA_PROFILES":
                return {"status": "SUCCEEDED", "result": {"operation": command_type, "profiles": profile_results}, "errorCode": None, "errorMessage": None}
            requested_token = str(payload.get("profileToken") or "")
            selected = next((item for item in profiles if item.token == requested_token), None) if requested_token else (profiles[0] if profiles else None)
            if selected is None:
                return {"status": "FAILED", "errorCode": "ONVIF_PROFILE_NOT_FOUND", "errorMessage": "Requested ONVIF media profile was not found."}
            stream = await client.get_stream_uri(selected.token)
            if command_type == "GET_ONVIF_STREAM_URI":
                return {"status": "SUCCEEDED", "result": {"operation": command_type, "profileToken": selected.token, "stream": stream}, "errorCode": None, "errorMessage": None}
            checks = {"networkReachable": True, "authentication": True, "deviceInformation": False, "mediaService": bool(client.media_service_url), "profiles": bool(profiles), "streamUri": bool(stream.get("uri")), "rtsp": False}
            device_info = await client.get_device_information()
            checks["deviceInformation"] = True
            rtsp_result = await rtsp_verify(stream["uri"], username=str(payload.get("username") or ""), password=str(payload.get("password") or ""), timeout=min(settings.rtsp_timeout_seconds, timeout))
            checks["rtsp"] = rtsp_result.get("status") == "VERIFIED_CONNECTED"
            return {"status": "SUCCEEDED", "result": {"operation": command_type, "verified": all(checks.values()), "verificationStatus": "VERIFIED" if all(checks.values()) else "PARTIALLY_VERIFIED", "checks": checks, "device": device_info, "profiles": profile_results, "stream": {"protocol": stream.get("protocol"), "timeout": stream.get("timeout")}, "rtsp": _sanitize_result(rtsp_result)}, "errorCode": None, "errorMessage": None}
        except OnvifError as exc:
            return {"status": "FAILED", "errorCode": exc.code, "errorMessage": exc.message}
    if command_type == "TEST_RTSP":
        url = str(payload.get("url") or "")
        if not url:
            return {"status": "FAILED", "errorCode": "INVALID_URL", "errorMessage": "No RTSP URL provided."}
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "rtsp" or not parsed.hostname:
            return {"status": "FAILED", "errorCode": "INVALID_URL", "errorMessage": "RTSP URL validation failed."}
        result = await asyncio.wait_for(rtsp_verify(url, username=str(payload.get("username") or ""), password=str(payload.get("password") or ""), timeout=min(5.0, settings.rtsp_timeout_seconds)), min(timeout, settings.rtsp_timeout_seconds + 2.0))
        return {"status": result.get("status", "FAILED"), "result": _sanitize_result(result), "errorCode": result.get("failureCode"), "errorMessage": result.get("message") or None}
    return {"status": "FAILED", "errorCode": "INVALID_COMMAND", "errorMessage": f"Unsupported command: {command_type}"}


async def execute_command(command: dict) -> dict:
    started = time.monotonic()
    try:
        result = await asyncio.wait_for(execute_onvif_operation(command, float(command.get("timeoutSeconds") or settings.command_timeout_seconds)), float(command.get("timeoutSeconds") or settings.command_timeout_seconds))
        result = _sanitize_result(result)
        return {"status": result.get("status", "FAILED"), "result": result.get("result", {}), "errorCode": result.get("errorCode"), "errorMessage": result.get("errorMessage"), "durationMs": round((time.monotonic() - started) * 1000)}
    except asyncio.TimeoutError:
        return {"status": "TIMEOUT", "result": {}, "errorCode": "COMMAND_TIMEOUT", "errorMessage": "The command exceeded the configured execution deadline.", "durationMs": round((time.monotonic() - started) * 1000)}
    except Exception as exc:  # pragma: no cover - defensive guard
        return {"status": "FAILED", "result": {}, "errorCode": "FAILED", "errorMessage": str(exc), "durationMs": round((time.monotonic() - started) * 1000)}
