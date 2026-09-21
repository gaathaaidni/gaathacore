# Observability

Status: PARTIALLY IMPLEMENTED.

A lightweight API metrics service and Stream Gateway `/metrics` endpoint track counters such as active cameras, frames received, dropped, processed, and queue depth. Production deployments should export these to Prometheus and enforce structured log redaction for RTSP passwords, JWTs, MinIO secrets, and internal tokens.
