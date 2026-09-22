import logging
import asyncio
import jwt
from fastapi import FastAPI, HTTPException, Depends, Header, status
from contextlib import asynccontextmanager
from typing import Annotated, Callable
from pydantic import BaseModel
import aiohttp

from config import settings
from camera_manager import CameraStreamManager
from media_paths import media_path_parts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stream_manager = CameraStreamManager()
metrics = {
    "frames_received": 0,
    "frames_dropped": 0,
    "frames_processed": 0,
    "queue_depth": 0,
    "stream_reconnects": 0,
}

class MediaAuthRequest(BaseModel):
    token: str = ''
    action: str
    path: str
    protocol: str = ''

async def _current_camera(camera_id: str):
    try:
        async with aiohttp.ClientSession(headers={"X-Internal-Token": settings.STREAM_GATEWAY_INTERNAL_TOKEN}) as session:
            async with session.get(f"{settings.API_URL}/cameras/internal/{camera_id}") as response:
                return await response.json() if response.status == 200 else None
    except aiohttp.ClientError:
        return None

async def verify_internal_token(x_internal_token: Annotated[str, Header()]):
    if x_internal_token != settings.STREAM_GATEWAY_INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal token")


def scoped_authorization(operation: str) -> Callable:
    async def verify(camera_id: str, authorization: Annotated[str | None, Header()] = None):
        secret = settings.STREAM_GATEWAY_AUTH_SECRET
        if not secret or not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Scoped stream authorization required")
        try:
            claims = jwt.decode(
                authorization[7:].strip(),
                secret,
                algorithms=["HS256"],
                audience="sentira-stream-gateway",
                issuer="sentira-api",
            )
        except (jwt.InvalidTokenError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid scoped stream authorization")
        if claims.get("cameraId") != camera_id or claims.get("operation") != operation:
            raise HTTPException(status_code=403, detail="Stream authorization scope mismatch")
        if not claims.get("organizationId") or not claims.get("siteId") or not claims.get("sub") or not claims.get("jti"):
            raise HTTPException(status_code=403, detail="Stream authorization scope is incomplete")
        camera = stream_manager.camera_configs.get(camera_id)
        if not camera or camera.get("organizationId") != claims["organizationId"] or camera.get("siteId") != claims["siteId"]:
            raise HTTPException(status_code=404, detail="Camera not found in authorized scope")
        return claims
    return verify

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Stream Gateway starting up...")
    asyncio.create_task(stream_manager.load_and_start_cameras())
    yield
    logger.info("Stream Gateway shutting down...")
    await stream_manager.stop_all_streams()

app = FastAPI(title="Sentira AI - Stream Gateway", lifespan=lifespan)

@app.post('/media/auth', status_code=status.HTTP_204_NO_CONTENT)
async def authorize_media(request: MediaAuthRequest):
    parts = media_path_parts(request.path)
    if not parts:
        raise HTTPException(status_code=403, detail='Invalid media path')

    organization_id, site_id, camera_id = parts
    if request.action == 'publish':
        if not settings.SENTIRA_FIXTURE_PUBLISH_TOKEN or request.token != settings.SENTIRA_FIXTURE_PUBLISH_TOKEN:
            raise HTTPException(status_code=403, detail='Media publication is not authorized')
        return None
    if request.action != 'read' or request.protocol not in {'hls', 'webrtc'} or not request.token:
        raise HTTPException(status_code=401, detail='Media authorization required')

    try:
        claims = jwt.decode(request.token, settings.STREAM_GATEWAY_AUTH_SECRET, algorithms=['HS256'], audience='sentira-stream-gateway', issuer='sentira-api')
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail='Invalid media authorization')

    if claims.get('operation') != 'playback' or claims.get('organizationId') != organization_id or claims.get('siteId') != site_id or claims.get('cameraId') != camera_id or not claims.get('sub') or not claims.get('jti'):
        raise HTTPException(status_code=403, detail='Media authorization scope mismatch')

    camera = await _current_camera(camera_id)
    if not camera or not camera.get('isEnabled') or camera.get('organizationId') != organization_id or camera.get('siteId') != site_id:
        raise HTTPException(status_code=403, detail='Camera is not currently authorized')
    return None

@app.get("/health", status_code=200)
async def health_check():
    statuses = stream_manager.get_all_statuses()
    return {
        "status": "ok",
        "webrtc": settings.WEBRTC_ENABLED,
        "hls": settings.HLS_ENABLED,
        "activeStreams": len(statuses),
        "maxActiveStreams": settings.MAX_ACTIVE_STREAMS,
    }

@app.get("/metrics")
async def get_metrics():
    statuses = stream_manager.get_all_statuses()
    return {
        **metrics,
        "active_streams": len(statuses),
        "max_active_streams": settings.MAX_ACTIVE_STREAMS,
    }

def playback(camera_id: str):
    return {
        "cameraId": camera_id,
        "preferred": "webrtc" if settings.WEBRTC_ENABLED else "hls",
        "webrtc": {
            "provider": settings.WEBRTC_PROVIDER,
            "whepUrl": f"/webrtc/{camera_id}/whep",
        } if settings.WEBRTC_ENABLED else None,
        "hls": {
            "url": f"/hls/{camera_id}/index.m3u8",
        } if settings.HLS_ENABLED else None,
    }

@app.get("/streams/{camera_id}/playback", dependencies=[Depends(scoped_authorization("playback"))])
async def get_playback(camera_id: str):
    return playback(camera_id)

@app.post("/streams/{camera_id}/start", dependencies=[Depends(scoped_authorization("start"))])
async def start_stream(camera_id: str):
    statuses = stream_manager.get_all_statuses()
    if camera_id not in statuses and len(statuses) >= settings.MAX_ACTIVE_STREAMS:
        raise HTTPException(status_code=429, detail="MAX_ACTIVE_STREAMS reached")
    success = await stream_manager.start_stream_by_id(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found or failed to start")
    return {"message": f"Stream for camera {camera_id} started."}

@app.post("/streams/{camera_id}/stop", dependencies=[Depends(scoped_authorization("stop"))])
async def stop_stream(camera_id: str):
    success = await stream_manager.stop_stream_by_id(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": f"Stream for camera {camera_id} stopped."}

@app.get("/streams", dependencies=[Depends(verify_internal_token)])
async def get_all_streams_status():
    return stream_manager.get_all_statuses()


@app.get("/streams/{camera_id}/status", dependencies=[Depends(scoped_authorization("status"))])
async def get_stream_status(camera_id: str):
    status = stream_manager.get_all_statuses().get(camera_id)
    if not status:
        raise HTTPException(status_code=404, detail="Camera stream status not found")
    return status
