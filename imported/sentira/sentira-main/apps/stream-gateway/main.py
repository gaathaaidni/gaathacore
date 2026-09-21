import logging
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Header
from contextlib import asynccontextmanager
from typing import Annotated

from config import settings
from camera_manager import CameraStreamManager

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

async def verify_internal_token(x_internal_token: Annotated[str, Header()]):
    if x_internal_token != settings.STREAM_GATEWAY_INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Stream Gateway starting up...")
    asyncio.create_task(stream_manager.load_and_start_cameras())
    yield
    logger.info("Stream Gateway shutting down...")
    await stream_manager.stop_all_streams()

app = FastAPI(title="Sentira AI - Stream Gateway", lifespan=lifespan)

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

@app.get("/streams/{camera_id}/playback", dependencies=[Depends(verify_internal_token)])
async def get_playback(camera_id: str):
    return playback(camera_id)

@app.post("/streams/{camera_id}/start", dependencies=[Depends(verify_internal_token)])
async def start_stream(camera_id: str):
    statuses = stream_manager.get_all_statuses()
    if camera_id not in statuses and len(statuses) >= settings.MAX_ACTIVE_STREAMS:
        raise HTTPException(status_code=429, detail="MAX_ACTIVE_STREAMS reached")
    success = await stream_manager.start_stream_by_id(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found or failed to start")
    return {"message": f"Stream for camera {camera_id} started."}

@app.post("/streams/{camera_id}/stop", dependencies=[Depends(verify_internal_token)])
async def stop_stream(camera_id: str):
    success = await stream_manager.stop_stream_by_id(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": f"Stream for camera {camera_id} stopped."}

@app.get("/streams", dependencies=[Depends(verify_internal_token)])
async def get_all_streams_status():
    return stream_manager.get_all_statuses()
