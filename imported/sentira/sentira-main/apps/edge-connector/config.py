import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_url: str = os.getenv("SENTIRA_API_URL", "http://localhost:4000/api")
    setup_session_id: str = os.getenv("SENTIRA_SETUP_SESSION_ID", "")
    pairing_code: str = os.getenv("SENTIRA_PAIRING_CODE", "")
    token_file: str = os.getenv("SENTIRA_CONNECTOR_TOKEN_FILE", "~/.config/sentira-edge/identity")
    connector_name: str = os.getenv("SENTIRA_CONNECTOR_NAME", "Sentira Edge Connector")
    connector_version: str = os.getenv("SENTIRA_CONNECTOR_VERSION", "13.2.0")
    heartbeat_seconds: float = float(os.getenv("CONNECTOR_HEARTBEAT_SECONDS", "15"))
    request_timeout_seconds: float = float(os.getenv("CONNECTOR_REQUEST_TIMEOUT_SECONDS", "10"))
    discovery_timeout_seconds: float = float(os.getenv("CONNECTOR_DISCOVERY_TIMEOUT_SECONDS", "15"))
    discovery_max_results: int = int(os.getenv("CONNECTOR_DISCOVERY_MAX_RESULTS", "64"))
    discovery_max_addresses: int = int(os.getenv("CONNECTOR_DISCOVERY_MAX_ADDRESSES", "256"))
    discovery_concurrency: int = int(os.getenv("CONNECTOR_DISCOVERY_CONCURRENCY", "32"))
    rtsp_timeout_seconds: float = float(os.getenv("CONNECTOR_RTSP_TIMEOUT_SECONDS", "5"))
    poll_interval_seconds: float = float(os.getenv("SENTIRA_POLL_INTERVAL_SECONDS", "10"))
    poll_max_wait_seconds: float = float(os.getenv("SENTIRA_POLL_MAX_WAIT_SECONDS", "20"))
    command_timeout_seconds: float = float(os.getenv("SENTIRA_COMMAND_TIMEOUT_SECONDS", "120"))
    max_command_batch: int = int(os.getenv("SENTIRA_COMMAND_BATCH_SIZE", "5"))
    onvif_timeout_seconds: float = float(os.getenv("SENTIRA_ONVIF_TIMEOUT_SECONDS", "15"))
    onvif_retry_count: int = int(os.getenv("SENTIRA_ONVIF_RETRY_COUNT", "1"))
    onvif_retry_delay_seconds: float = float(os.getenv("SENTIRA_ONVIF_RETRY_DELAY_SECONDS", "0.25"))
    max_hosts: int = int(os.getenv("SENTIRA_MAX_HOSTS", "64"))
    max_concurrent_network_probes: int = int(os.getenv("SENTIRA_MAX_CONCURRENT_NETWORK_PROBES", "8"))


settings = Settings()
