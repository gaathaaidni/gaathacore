import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    API_URL = os.getenv("SENTIRA_API_URL", "http://localhost:4000/api")
    STREAM_GATEWAY_INTERNAL_TOKEN = os.getenv("STREAM_GATEWAY_INTERNAL_TOKEN", "")
    AI_WORKER_INGEST_TOKEN = os.getenv("AI_WORKER_INGEST_TOKEN", "")

    # AI Frame Pipeline settings
    AI_FRAME_RATE = int(os.getenv("AI_FRAME_RATE", "2"))
    AI_JPEG_QUALITY = int(os.getenv("AI_JPEG_QUALITY", "80"))

    # Rolling Buffer settings
    SEGMENT_SECONDS = int(os.getenv("SEGMENT_SECONDS", "2"))
    BUFFER_RETENTION_SECONDS = int(os.getenv("BUFFER_RETENTION_SECONDS", "120"))
    BUFFER_ROOT = os.getenv("BUFFER_ROOT", "/var/lib/sentira/buffer")
    AI_WORKER_URL = os.getenv("AI_WORKER_URL", "http://ai-worker:8002")

    # Phase 5 scalability and playback settings
    MAX_ACTIVE_STREAMS = int(os.getenv("MAX_ACTIVE_STREAMS", "25"))
    MAX_FRAME_QUEUE = int(os.getenv("MAX_FRAME_QUEUE", "200"))
    WEBRTC_ENABLED = os.getenv("WEBRTC_ENABLED", "true").lower() == "true"
    WEBRTC_PROVIDER = os.getenv("WEBRTC_PROVIDER", "mediamtx")
    HLS_ENABLED = os.getenv("HLS_ENABLED", "true").lower() == "true"

settings = Settings()
# Phase 7 reliability defaults
Settings.STREAM_TIMEOUT_SECONDS = int(os.getenv("STREAM_TIMEOUT_SECONDS", "15"))
Settings.STREAM_MAX_RECONNECT_DELAY_SECONDS = int(os.getenv("STREAM_MAX_RECONNECT_DELAY_SECONDS", "60"))
