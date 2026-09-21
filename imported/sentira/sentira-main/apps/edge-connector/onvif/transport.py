from typing import Protocol

import aiohttp


class SoapTransport(Protocol):
    async def post(self, url: str, body: bytes, timeout: float, username: str = "", password: str = "") -> bytes:
        ...


class AiohttpSoapTransport:
    async def post(self, url: str, body: bytes, timeout: float, username: str = "", password: str = "") -> bytes:
        auth = aiohttp.BasicAuth(username, password) if username and password else None
        request_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=request_timeout, raise_for_status=False) as session:
            async with session.post(url, data=body, headers={"Content-Type": "application/soap+xml; charset=utf-8"}, auth=auth, allow_redirects=False) as response:
                data = await response.read()
                if response.status in (401, 403):
                    raise PermissionError("ONVIF authentication failed")
                if response.status >= 400:
                    raise RuntimeError("ONVIF service returned an HTTP error")
                return data
