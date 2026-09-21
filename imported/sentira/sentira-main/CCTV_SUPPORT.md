# CCTV Support Escalation

Customers can request help from every guided setup failure state. `POST /api/cctv/support-requests` creates a tenant-scoped request containing the setup session, device identification, current step, selected answers, and structured test result when available.

Support request states are `OPEN`, `TRIAGED`, `IN_PROGRESS`, `WAITING_FOR_CUSTOMER`, `RESOLVED`, and `CLOSED`. Reasons include setup help, incompatibility, DVR/NVR setup, network, authentication, stream, and discovery failures.

The API removes keys containing `password`, `token`, `secret`, `privateKey`, `authorization`, or `credential` from nested context before persistence and audit logging. Camera passwords are never returned by camera APIs and must not be added to support messages.

The current foundation stores assignment and resolution fields. A future support console can add workflows without changing the customer setup contract.
