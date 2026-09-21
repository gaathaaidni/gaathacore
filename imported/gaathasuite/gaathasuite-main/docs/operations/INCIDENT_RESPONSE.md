# Incident Response

**Status:** IMPLEMENTED as an internal procedure.

Use: **Detect -> Stabilize -> Investigate -> Mitigate -> Recover -> Verify -> Document -> Prevent recurrence**.

For application outage check containers, Nginx, `/health`, `/ready`, logs, and recent deploys. For database/Redis incidents check service health and connectivity. For CPU/memory/disk incidents stabilize traffic and capacity before changing data. For migration failure stop rollout and restore the reviewed backup plan. For auth or suspected security incidents preserve logs, revoke/rotate affected credentials where supported, restrict access, and escalate to the configured security contact. DNS/TLS incidents require provider, certificate, and Nginx checks.

`SECURITY_CONTACT_EMAIL: [TO BE CONFIGURED]`
