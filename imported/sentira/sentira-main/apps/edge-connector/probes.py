import asyncio
import base64
import ipaddress
import socket
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class ProbeResult:
    name: str
    localAddress: str
    protocol: str
    discoveryStatus: str
    capabilities: dict
    manufacturer: Optional[str] = None
    model: Optional[str] = None


def redact_url(value: str) -> str:
    parts = urlsplit(value)
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    return urlunsplit((parts.scheme, f"{host}{port}", parts.path, parts.query, ""))


def validate_endpoint(host: str, allow_lan: bool = True) -> str:
    addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    if not addresses:
        raise ValueError("RTSP_UNREACHABLE")
    address = ipaddress.ip_address(addresses[0][4][0])
    if address.is_unspecified or address.is_loopback or address.is_multicast or address.is_reserved:
        raise ValueError("RTSP_FORBIDDEN_DESTINATION")
    if not allow_lan and (address.is_private or address.is_link_local):
        raise ValueError("RTSP_PRIVATE_DESTINATION")
    return str(address)


async def rtsp_verify(url: str, username: str = "", password: str = "", timeout: float = 5) -> dict:
    started = time.monotonic()
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "rtsp" or parsed.username or parsed.password or not parsed.hostname:
        return {"status": "FAILED", "failureCode": "RTSP_INVALID_RESPONSE", "protocol": "RTSP"}
    try:
        address = validate_endpoint(parsed.hostname)
        reader, writer = await asyncio.wait_for(asyncio.open_connection(address, parsed.port or 554), timeout)
        authority = f"{parsed.hostname}:{parsed.port or 554}"
        headers = [f"CSeq: 1", "User-Agent: Sentira-Edge-Connector/13.1"]
        if username:
            headers.append("Authorization: Basic " + base64.b64encode(f"{username}:{password}".encode()).decode())
        request = f"OPTIONS rtsp://{authority}{parsed.path or '/'} RTSP/1.0\r\n" + "\r\n".join(headers) + "\r\n\r\n"
        writer.write(request.encode())
        await writer.drain()
        response = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout)
        status_line = response.splitlines()[0].decode("ascii", "replace")
        code = int(status_line.split()[1]) if len(status_line.split()) > 1 else 0
        if code in (401, 403):
            result = {"status": "FAILED", "failureCode": "RTSP_AUTH_FAILED", "protocol": "RTSP"}
        elif not 200 <= code < 300:
            result = {"status": "FAILED", "failureCode": "RTSP_INVALID_RESPONSE", "protocol": "RTSP"}
        else:
            result = {"status": "VERIFIED_CONNECTED", "protocol": "RTSP", "streamAvailable": True, "address": address}
        writer.close()
        await writer.wait_closed()
        result["latencyMs"] = round((time.monotonic() - started) * 1000)
        return result
    except asyncio.TimeoutError:
        return {"status": "FAILED", "failureCode": "RTSP_TIMEOUT", "protocol": "RTSP"}
    except (OSError, ValueError):
        return {"status": "FAILED", "failureCode": "RTSP_UNREACHABLE", "protocol": "RTSP"}


async def onvif_discover(timeout: float = 5, max_results: int = 64) -> list[dict]:
    message_id = f"urn:uuid:{uuid.uuid4()}"
    body = f'''<?xml version="1.0" encoding="UTF-8"?><e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" xmlns:dn="http://www.onvif.org/ver10/network/wsdl"><e:Header><w:MessageID>{message_id}</w:MessageID><w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To><w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action></e:Header><e:Body><d:Probe><d:Types>dn:NetworkVideoTransmitter</d:Types></d:Probe></e:Body></e:Envelope>'''.encode()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    class DiscoveryProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data: bytes, _address: tuple[str, int]) -> None:
            if not queue.full():
                queue.put_nowait(data)

    transport, _protocol = await loop.create_datagram_endpoint(DiscoveryProtocol, local_addr=("0.0.0.0", 0))
    results: list[dict] = []
    try:
        transport.sendto(body, ("239.255.255.250", 3702))
        end = loop.time() + timeout
        while len(results) < max_results and loop.time() < end:
            try:
                data = await asyncio.wait_for(queue.get(), max(0.01, end - loop.time()))
            except asyncio.TimeoutError:
                break
            text = data.decode("utf-8", "ignore")
            addresses = {value for value in text.replace("\n", " ").split() if value.startswith(("http://", "https://"))}
            for address in addresses:
                host = urlsplit(address).hostname
                if host and host not in {item.get("localAddress") for item in results}:
                    results.append({"name": "ONVIF device", "localAddress": host, "protocol": "ONVIF", "discoveryStatus": "READY", "capabilities": {"ONVIF": True}, "deviceServiceUrl": redact_url(address)})
        return results
    finally:
        transport.close()


def network_addresses(network: str, max_addresses: int) -> list[str]:
    subnet = ipaddress.ip_network(network, strict=False)
    if subnet.num_addresses > max_addresses:
        raise ValueError("DISCOVERY_LIMIT_REACHED")
    return [str(address) for address in subnet.hosts()][:max_addresses]


async def bounded_rtsp_probe(addresses: list[str], port: int = 554, concurrency: int = 32, timeout: float = 1) -> list[dict]:
    semaphore = asyncio.Semaphore(concurrency)

    async def probe(address: str) -> Optional[dict]:
        async with semaphore:
            result = await rtsp_verify(f"rtsp://{address}:{port}/", timeout=timeout)
            return {"name": f"RTSP device {address}", "localAddress": address, "protocol": "RTSP", "discoveryStatus": "READY", "capabilities": {"RTSP": result}} if result["status"] == "VERIFIED_CONNECTED" else None

    found = await asyncio.gather(*(probe(address) for address in addresses))
    return [item for item in found if item is not None]
