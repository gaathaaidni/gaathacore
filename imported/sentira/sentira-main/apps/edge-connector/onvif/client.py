import asyncio
import ipaddress
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from .auth import username_token
from .exceptions import OnvifError
from .models import OnvifCredentials, OnvifProfile
from .soap import child, children, parse_response, request, text
from .transport import AiohttpSoapTransport, SoapTransport

DEVICE_NS = "http://www.onvif.org/ver10/device/wsdl"
MEDIA_NS = "http://www.onvif.org/ver10/media/wsdl"
MEDIA2_NS = "http://www.onvif.org/ver20/media/wsdl"


class OnvifClient:
    def __init__(self, endpoint: str, credentials: OnvifCredentials | None = None, timeout: float = 15, transport: SoapTransport | None = None, retries: int = 1, retry_delay: float = 0.25) -> None:
        self.endpoint = self._validate_endpoint(endpoint)
        self.credentials = credentials or OnvifCredentials()
        self.timeout = timeout
        self.transport = transport or AiohttpSoapTransport()
        self.retries = max(0, min(retries, 3))
        self.retry_delay = max(0.0, min(retry_delay, 5.0))
        self.device_service_url = self.endpoint
        self.media_service_url: str | None = None

    @staticmethod
    def _validate_endpoint(endpoint: str) -> str:
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise OnvifError("ONVIF_SERVICE_UNAVAILABLE", "ONVIF device endpoint is invalid")
        try:
            port = parsed.port
        except ValueError as exc:
            raise OnvifError("ONVIF_SERVICE_UNAVAILABLE", "ONVIF device endpoint is invalid") from exc
        if port is not None and not 1 <= port <= 65535:
            raise OnvifError("ONVIF_SERVICE_UNAVAILABLE", "ONVIF device endpoint is invalid")
        try:
            address = ipaddress.ip_address(parsed.hostname)
            if address.is_multicast or address.is_unspecified or address.is_reserved:
                raise OnvifError("ONVIF_SERVICE_UNAVAILABLE", "ONVIF device endpoint is not allowed")
        except ValueError:
            pass
        return endpoint

    async def _call(self, url: str, action: str, operation: str, body_xml: str = "") -> ET.Element:
        security = username_token(self.credentials.username, self.credentials.password, self.credentials.digest) if self.credentials.username else b""
        body = request(action, operation, body_xml, security)
        try:
            response = None
            for attempt in range(self.retries + 1):
                try:
                    response = await asyncio.wait_for(self.transport.post(url, body, self.timeout, self.credentials.username, self.credentials.password), self.timeout)
                    break
                except (OSError, ConnectionError, asyncio.TimeoutError):
                    if attempt >= self.retries:
                        raise
                    await asyncio.sleep(self.retry_delay)
            if response is None:
                raise OSError("ONVIF request failed")
            return parse_response(response)
        except asyncio.TimeoutError as exc:
            raise OnvifError("ONVIF_TIMEOUT", "ONVIF request timed out") from exc
        except PermissionError as exc:
            raise OnvifError("ONVIF_AUTH_FAILED", "ONVIF authentication failed") from exc
        except (OSError, ConnectionError) as exc:
            raise OnvifError("ONVIF_DEVICE_UNREACHABLE", "ONVIF device could not be reached") from exc
        except RuntimeError as exc:
            raise OnvifError("ONVIF_SOAP_FAULT", "ONVIF SOAP request failed") from exc
        except ValueError as exc:
            raise OnvifError("ONVIF_INVALID_RESPONSE", "ONVIF returned an invalid response") from exc

    async def get_services(self) -> dict[str, str]:
        body = await self._call(self.device_service_url, "http://www.onvif.org/ver10/device/wsdl/GetServices", f"{{{DEVICE_NS}}}GetServices", '<IncludeCapability>false</IncludeCapability>')
        services: dict[str, str] = {}
        for service in children(body, "Service"):
            namespace = text(service, "Namespace")
            address = text(service, "XAddr")
            if namespace and address and namespace.startswith("http://www.onvif.org/ver10/device/wsdl"):
                services["device"] = address
            elif namespace and address and ("/ver10/media/wsdl" in namespace or "/ver20/media/wsdl" in namespace):
                services["media"] = address
        self.media_service_url = services.get("media")
        return services

    async def get_device_information(self) -> dict[str, str | None]:
        body = await self._call(self.device_service_url, "http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation", f"{{{DEVICE_NS}}}GetDeviceInformation")
        return {"manufacturer": text(body, "Manufacturer"), "model": text(body, "Model"), "firmware": text(body, "FirmwareVersion"), "serialNumber": text(body, "SerialNumber"), "hardwareId": text(body, "HardwareId")}

    async def get_profiles(self) -> list[OnvifProfile]:
        if not self.media_service_url:
            await self.get_services()
        if not self.media_service_url:
            raise OnvifError("ONVIF_SERVICE_UNAVAILABLE", "ONVIF media service could not be discovered")
        body = await self._call(self.media_service_url, "http://www.onvif.org/ver10/media/wsdl/GetProfiles", f"{{{MEDIA_NS}}}GetProfiles")
        profiles: list[OnvifProfile] = []
        for profile in children(body, "Profiles"):
            token = profile.attrib.get("token")
            if not token:
                continue
            source = child(profile, "VideoSourceConfiguration")
            encoder = child(profile, "VideoEncoderConfiguration")
            resolution_element = child(encoder, "Resolution") if encoder is not None else None
            width = text(resolution_element, "Width")
            height = text(resolution_element, "Height")
            fps_value = text(encoder, "FrameRateLimit") if encoder is not None else None
            try:
                fps = float(fps_value) if fps_value else None
            except ValueError:
                fps = None
            resolution = {"width": int(width), "height": int(height)} if width and height and width.isdigit() and height.isdigit() else None
            profiles.append(OnvifProfile(token, text(profile, "Name"), resolution, text(encoder, "Encoding") if encoder is not None else None, fps, {"token": source.attrib.get("token")} if source is not None and source.attrib.get("token") else None, {"token": encoder.attrib.get("token")} if encoder is not None and encoder.attrib.get("token") else None))
        return profiles

    async def get_stream_uri(self, profile_token: str) -> dict[str, str | None]:
        if not self.media_service_url:
            await self.get_services()
        if not self.media_service_url:
            raise OnvifError("ONVIF_SERVICE_UNAVAILABLE", "ONVIF media service could not be discovered")
        profiles = await self.get_profiles()
        if not any(profile.token == profile_token for profile in profiles):
            raise OnvifError("ONVIF_PROFILE_NOT_FOUND", "Requested ONVIF media profile was not found")
        body_xml = f'<ProfileToken>{escape(profile_token)}</ProfileToken>'
        body = await self._call(self.media_service_url, "http://www.onvif.org/ver10/media/wsdl/GetStreamUri", f"{{{MEDIA_NS}}}GetStreamUri", f'<StreamSetup><Stream xmlns="http://www.onvif.org/ver10/schema">RTP-Unicast</Stream><Transport xmlns="http://www.onvif.org/ver10/schema"><Protocol>RTSP</Protocol></Transport></StreamSetup>{body_xml}')
        uri = text(body, "Uri")
        if not uri:
            raise OnvifError("ONVIF_STREAM_URI_UNAVAILABLE", "ONVIF did not return a stream URI")
        return {"uri": self._redact_uri(uri), "protocol": text(body, "Protocol"), "timeout": text(body, "Timeout")}

    @staticmethod
    def _redact_uri(uri: str) -> str:
        parsed = urlsplit(uri)
        if not parsed.username and not parsed.password:
            return uri
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        return parsed._replace(netloc=f"{host}{port}").geturl()
