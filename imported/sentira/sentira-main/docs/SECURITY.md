# Phase 5 Security Review

Status: REVIEW COMPLETED / REMEDIATION PARTIAL.

Key findings: browser RTSP exposure must remain forbidden; camera URLs are SSRF-sensitive and require allow-list/network policy validation; evidence URLs must remain signed and audited; tenant-scoped queries and JWT/RBAC checks remain mandatory. Never log RTSP passwords, JWTs, MinIO secrets, RabbitMQ/Redis credentials, or internal service tokens.
