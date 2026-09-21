import asyncio
import json
import logging
import os
import socket
import time
from pathlib import Path

import aiohttp

from command_executor import execute_command
from config import settings

logger = logging.getLogger("sentira-edge-worker")


class EdgeWorker:
    def __init__(self) -> None:
        self.connector_id = ""
        self.token = ""
        self.session: aiohttp.ClientSession | None = None
        self.stop_event = asyncio.Event()

    def load_identity(self) -> bool:
        path = Path(settings.token_file).expanduser()
        try:
            payload = json.loads(path.read_text())
            self.connector_id = str(payload.get("connectorId", ""))
            self.token = str(payload.get("token", ""))
            return bool(self.connector_id and self.token)
        except (FileNotFoundError, OSError, ValueError, KeyError):
            return False

    def save_identity(self) -> None:
        path = Path(settings.token_file).expanduser()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_text(json.dumps({"connectorId": self.connector_id, "token": self.token}))
        os.chmod(path, 0o600)

    async def register(self) -> None:
        if not settings.setup_session_id or not settings.pairing_code:
            raise RuntimeError("SENTIRA_SETUP_SESSION_ID and SENTIRA_PAIRING_CODE are required for registration")
        assert self.session is not None
        payload = {"pairingCode": settings.pairing_code, "connectorName": settings.connector_name, "version": settings.connector_version}
        async with self.session.post(f"{settings.api_url}/cctv/setup-sessions/{settings.setup_session_id}/connector/register", json=payload) as response:
            data = await response.json()
            if response.status >= 300:
                raise RuntimeError(data.get("message", "connector registration failed"))
            self.connector_id = str(data["connectorId"])
            self.token = str(data["registrationToken"])
            self.save_identity()
        logger.info("registered connector=%s", self.connector_id)

    async def heartbeat(self) -> None:
        assert self.session is not None
        payload = {
            "connectorId": self.connector_id,
            "registrationToken": self.token,
            "metadata": {
                "capabilities": ["DISCOVERY", "RTSP", "ONVIF"],
                "hostname": socket.gethostname(),
                "platform": os.name,
                "version": settings.connector_version,
            },
        }
        async with self.session.post(f"{settings.api_url}/cctv/connectors/heartbeat", json=payload) as response:
            if response.status in (401, 403):
                raise RuntimeError("connector authentication failed")
            if response.status >= 300:
                raise RuntimeError("connector heartbeat failed")

    async def poll_commands(self) -> list[dict]:
        if not self.connector_id or not self.token:
            return []
        params = {
            "connectorId": self.connector_id,
            "registrationToken": self.token,
            "limit": settings.max_command_batch,
            "wait": min(int(settings.poll_max_wait_seconds), 20),
        }
        async with self.session.get(f"{settings.api_url}/cctv/connectors/me/commands", params=params) as response:
            if response.status in (401, 403):
                raise RuntimeError("connector authentication failed during command poll")
            if response.status >= 300:
                raise RuntimeError("command poll failed")
            data = await response.json()
            return data if isinstance(data, list) else []

    async def ack_command(self, command: dict) -> None:
        if not self.connector_id or not self.token:
            return
        url = f"{settings.api_url}/cctv/connectors/me/commands/{command['id']}/ack"
        payload = {"connectorId": self.connector_id, "registrationToken": self.token}
        async with self.session.post(url, json=payload) as response:
            if response.status >= 300:
                logger.warning("ack failed for command=%s status=%s", command.get("id"), response.status)

    async def report_result(self, command: dict, outcome: dict) -> None:
        if not self.connector_id or not self.token:
            return
        payload = {
            "connectorId": self.connector_id,
            "registrationToken": self.token,
            "status": outcome.get("status", "FAILED"),
            "result": outcome.get("result", {}),
            "errorCode": outcome.get("errorCode"),
            "errorMessage": outcome.get("errorMessage"),
            "startedAt": command.get("startedAt"),
            "completedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        async with self.session.post(f"{settings.api_url}/cctv/connectors/me/commands/{command['id']}/result", json=payload) as response:
            if response.status >= 300:
                logger.warning("result report failed for command=%s status=%s", command.get("id"), response.status)

    async def process_command(self, command: dict) -> None:
        try:
            await self.ack_command(command)
            command["startedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            outcome = await execute_command(command)
            await self.report_result(command, outcome)
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning("command execution failed: %s", exc)

    async def run(self) -> None:
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as self.session:
            if not self.load_identity():
                await self.register()
            while not self.stop_event.is_set():
                try:
                    await self.heartbeat()
                    for command in await self.poll_commands():
                        await self.process_command(command)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.warning("edge loop failed: %s", type(exc).__name__)
                try:
                    await asyncio.wait_for(self.stop_event.wait(), settings.poll_interval_seconds)
                except asyncio.TimeoutError:
                    pass
