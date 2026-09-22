import asyncio
import base64
import contextlib
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import aiohttp

from config import settings
from media_paths import media_path
from rolling_buffer import RollingBuffer

logger = logging.getLogger(__name__)

@dataclass
class CameraRuntimeStatus:
    camera_id: str; state: str = "CONNECTING"; reconnect_attempts: int = 0; fps: float = 0.0
    bitrate_kbps: Optional[float] = None; latency_ms: Optional[float] = None; health_score: int = 0
    last_heartbeat_at: Optional[float] = None; last_frame_at: Optional[float] = None; error_classification: Optional[str] = None

class CameraStreamManager:
    def __init__(self):
        self.streams: Dict[str, asyncio.Task] = {}; self.camera_configs: Dict[str, dict] = {}; self.statuses: Dict[str, CameraRuntimeStatus] = {}
        self.processes: Dict[str, list[asyncio.subprocess.Process]] = {}
        self.max_reconnect_delay = int(settings.STREAM_MAX_RECONNECT_DELAY_SECONDS); self.stream_timeout = int(settings.STREAM_TIMEOUT_SECONDS)

    async def _fetch_all_cameras(self):
        try:
            async with aiohttp.ClientSession(headers={"X-Internal-Token": settings.STREAM_GATEWAY_INTERNAL_TOKEN}) as session:
                async with session.get(f"{settings.API_URL}/cameras/internal/all") as response:
                    return await response.json() if response.status == 200 else []
        except aiohttp.ClientError as exc: logger.error("camera discovery unavailable: %s", exc); return []

    async def load_and_start_cameras(self):
        for camera in await self._fetch_all_cameras():
            self.camera_configs[camera['id']] = camera
            if camera.get('isEnabled') and camera.get('aiEnabled', True): await self.start_stream_by_id(camera['id'])

    async def start_stream_by_id(self, camera_id: str) -> bool:
        if camera_id in self.streams and not self.streams[camera_id].done(): return True
        if camera_id not in self.camera_configs: return False
        self.statuses[camera_id] = CameraRuntimeStatus(camera_id=camera_id)
        self.streams[camera_id] = asyncio.create_task(self._supervise_camera(camera_id), name=f"camera-{camera_id}")
        return True

    async def _supervise_camera(self, camera_id: str):
        status = self.statuses[camera_id]
        while self.camera_configs.get(camera_id, {}).get('isEnabled', True):
            try:
                status.state = "CONNECTING"; await self._run_ffmpeg(camera_id); status.reconnect_attempts = 0
            except asyncio.CancelledError: raise
            except Exception as exc:
                status.state = "STREAM_ERROR"; status.health_score = 0; status.error_classification = type(exc).__name__; status.reconnect_attempts += 1
                delay = min(self.max_reconnect_delay, 2 ** min(status.reconnect_attempts, 6)); logger.warning("camera %s reconnect in %ss: %s", camera_id, delay, exc); await asyncio.sleep(delay)
            finally: await self._terminate_processes(camera_id)
        status.state = "DISABLED"

    async def _run_ffmpeg(self, camera_id: str):
        camera = self.camera_configs[camera_id]; source = camera.get('streamUrl')
        if not source: raise RuntimeError("camera has no stream URL")
        buffer = RollingBuffer(settings.BUFFER_ROOT, camera_id, settings.SEGMENT_SECONDS, settings.BUFFER_RETENTION_SECONDS)
        self.processes[camera_id] = []
        frame_proc = await asyncio.create_subprocess_exec('ffmpeg', '-nostdin', '-loglevel', 'error', '-rtsp_transport', 'tcp', '-i', source, '-vf', f'fps={settings.AI_FRAME_RATE}', '-f', 'image2pipe', '-vcodec', 'mjpeg', 'pipe:1', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self.processes[camera_id].append(frame_proc)
        segment_proc = await asyncio.create_subprocess_exec('ffmpeg', '-nostdin', '-loglevel', 'error', '-rtsp_transport', 'tcp', '-i', source, '-c', 'copy', '-f', 'segment', '-segment_time', str(settings.SEGMENT_SECONDS), '-strftime', '1', '-reset_timestamps', '1', buffer.pattern(), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
        self.processes[camera_id].append(segment_proc)
        publication_proc = await asyncio.create_subprocess_exec(*self._media_publication_command(camera), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
        self.processes[camera_id].append(publication_proc)
        status = self.statuses[camera_id]; status.state = 'ONLINE'; status.health_score = 100
        started, frames, last_cleanup = time.monotonic(), 0, time.monotonic()
        while True:
            if any(proc.returncode is not None for proc in self.processes[camera_id]): raise RuntimeError('ffmpeg exited')
            jpeg = await self._read_jpeg(frame_proc.stdout)
            if not jpeg: raise RuntimeError('ffmpeg frame stream ended')
            now = time.monotonic(); frames += 1; status.last_frame_at = now; status.last_heartbeat_at = now; status.fps = frames / max(now - started, .001)
            await self._publish_frame(camera, jpeg)
            if now - last_cleanup >= settings.SEGMENT_SECONDS: await buffer.cleanup(); last_cleanup = now

    def _media_publication_command(self, camera: dict) -> list[str]:
        path = media_path(camera['organizationId'], camera['siteId'], camera['id'])
        target = f"{settings.MEDIAMTX_RTSP_URL.rstrip('/')}/{path}"
        token = settings.SENTIRA_MEDIA_PUBLISH_TOKEN
        if token:
            target = f"{target}?token={token}"
        return ['ffmpeg', '-nostdin', '-loglevel', 'error', '-rtsp_transport', 'tcp', '-i', camera['streamUrl'], '-c', 'copy', '-f', 'rtsp', '-rtsp_transport', 'tcp', target]

    async def _read_jpeg(self, stream):
        data = bytearray()
        while True:
            chunk = await asyncio.wait_for(stream.read(4096), timeout=self.stream_timeout)
            if not chunk: return None
            data.extend(chunk); end = data.find(b'\xff\xd9')
            if end >= 0: return bytes(data[:end + 2])

    async def _publish_frame(self, camera: dict, jpeg: bytes):
        payload = {'organizationId': camera['organizationId'], 'siteId': camera['siteId'], 'cameraId': camera['id'], 'frameId': str(uuid.uuid4()), 'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(), 'jpegBase64': base64.b64encode(jpeg).decode()}
        async with aiohttp.ClientSession(headers={"X-AI-Worker-Token": settings.AI_WORKER_INGEST_TOKEN}) as session:
            async with session.post(f"{settings.AI_WORKER_URL}/frames", json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status >= 300: raise RuntimeError(f'ai worker rejected frame: {response.status}')

    async def _terminate_processes(self, camera_id: str):
        for proc in self.processes.pop(camera_id, []):
            if proc.returncode is None:
                proc.terminate()
                with contextlib.suppress(asyncio.TimeoutError): await asyncio.wait_for(proc.wait(), 5)
                if proc.returncode is None: proc.kill(); await proc.wait()

    async def stop_stream_by_id(self, camera_id: str) -> bool:
        task = self.streams.get(camera_id)
        if not task or task.done(): return False
        task.cancel(); await asyncio.gather(task, return_exceptions=True); await self._terminate_processes(camera_id); self.streams.pop(camera_id, None); self.statuses[camera_id].state = 'OFFLINE'; return True
    async def stop_all_streams(self): await asyncio.gather(*(self.stop_stream_by_id(cid) for cid in list(self.streams)), return_exceptions=True)
    def get_all_statuses(self): return {cid: asdict(status) for cid, status in self.statuses.items()}
