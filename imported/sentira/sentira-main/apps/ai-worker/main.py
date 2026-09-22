"""CPU-safe inference ingress and durable RabbitMQ detection publisher."""
from __future__ import annotations

import base64
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

try:
    import pika
except ModuleNotFoundError:  # Allows pure model tests on hosts without worker dependencies.
    pika = None
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from models import ConfigurableModelProvider

log = logging.getLogger("sentira.ai-worker")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

class Frame(BaseModel):
    organizationId: str
    siteId: str
    cameraId: str
    frameId: str
    timestamp: str
    jpegBase64: str = Field(min_length=1)
    correlationId: str | None = None


def require_ingest_auth(token: str | None = Header(default=None, alias="X-AI-Worker-Token")) -> None:
    expected = os.getenv("AI_WORKER_INGEST_TOKEN", "")
    if not expected or not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid worker authentication")

class RabbitPublisher:
    def __init__(self) -> None:
        self.url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
        self.connection: pika.BlockingConnection | None = None
        self.channel: Any = None

    def _channel(self):
        if pika is None:
            raise RuntimeError("pika is required to publish detections; install requirements.txt")
        if self.connection is None or self.connection.is_closed:
            params = pika.URLParameters(self.url)
            params.heartbeat = 30
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            self.channel.exchange_declare("sentira.detections", "direct", durable=True)
            self.channel.queue_declare("detection.queue", durable=True,
                arguments={"x-dead-letter-exchange": "sentira.detections.dlx", "x-dead-letter-routing-key": "detection.failed"})
            self.channel.exchange_declare("sentira.detections.dlx", "direct", durable=True)
            self.channel.queue_bind("detection.queue", "sentira.detections", "detection")
            self.channel.confirm_delivery()
        return self.channel

    def publish(self, payload: dict[str, Any]) -> None:
        try:
            tenant_id = str(payload.get("organizationId") or "").strip()
            if not tenant_id:
                raise ValueError("organizationId is required for a tenant-scoped detection job")
            self._channel().basic_publish("sentira.detections", "detection", json.dumps(payload).encode(),
                pika.BasicProperties(content_type="application/json", delivery_mode=pika.DeliveryMode.Persistent,
                                     message_id=payload["frameId"], timestamp=int(time.time()),
                                     headers={"x-tenant-id": tenant_id, "x-job-kind": "detection"}))
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self.connection and self.connection.is_open:
            self.connection.close()
        self.connection = None
        self.channel = None

provider = ConfigurableModelProvider()
publisher = RabbitPublisher()
app = FastAPI(title="Sentira AI Worker")

def deterministic_objects(frame: Frame) -> list[dict[str, Any]]:
    """Integration-only provider: fixed, explicitly selected CPU result."""
    if os.getenv("AI_PROVIDER", "deterministic") != "deterministic":
        return provider.predict(base64.b64decode(frame.jpegBase64), frame.cameraId)
    return [{"class_name": "person", "confidence": 0.95, "bbox": [0.1, 0.1, 0.3, 0.6]}]

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "HEALTHY", "provider": os.getenv("AI_PROVIDER", "deterministic")}

@app.post("/frames", status_code=202)
def infer(frame: Frame, _auth: None = Depends(require_ingest_auth)) -> dict[str, Any]:
    max_frame_bytes = int(os.getenv("AI_MAX_FRAME_BYTES", "10485760"))
    max_encoded_length = (max_frame_bytes * 4 // 3) + 4
    if len(frame.jpegBase64) > max_encoded_length:
        raise HTTPException(413, "JPEG frame exceeds configured size limit")
    if not all((frame.organizationId, frame.siteId, frame.cameraId, frame.frameId, frame.timestamp)):
        raise HTTPException(422, "Tenant and frame identifiers are required")
    try:
        raw_frame = base64.b64decode(frame.jpegBase64, validate=True)
    except ValueError as exc:
        raise HTTPException(422, "jpegBase64 is not valid base64") from exc
    if not raw_frame.startswith(b'\xff\xd8') or not raw_frame.endswith(b'\xff\xd9'):
        raise HTTPException(422, "jpegBase64 does not contain a JPEG frame")
    if len(raw_frame) > max_frame_bytes:
        raise HTTPException(413, "JPEG frame exceeds configured size limit")
    started = time.perf_counter()
    objects = deterministic_objects(frame)
    metadata = provider.metadata()
    detection = {
        "organizationId": frame.organizationId, "siteId": frame.siteId, "cameraId": frame.cameraId,
        "timestamp": frame.timestamp or datetime.now(timezone.utc).isoformat(), "frameId": frame.frameId,
        "model": metadata.name, "modelVersion": metadata.version,
        "processingTimeMs": round((time.perf_counter() - started) * 1000, 3), "objects": objects,
        "jpegBase64": frame.jpegBase64, "correlationId": frame.correlationId or frame.frameId,
    }
    try:
        publisher.publish(detection)
    except Exception as exc:
        log.exception("RabbitMQ publish failed")
        raise HTTPException(503, "detection transport unavailable") from exc
    return {"accepted": True, "frameId": frame.frameId}

@app.on_event("shutdown")
def shutdown() -> None:
    publisher.close()
