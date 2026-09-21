# RBAC

## IMPLEMENTED — NOT VERIFIED
Use role JSON permissions keyed by names such as `event.view`, `event.acknowledge`, `event.resolve`, `event.dismiss`, `analytics.view`, `reports.view`, and `audit.view`. `system.admin` overrides these permissions. The permission guard verifies authenticated user, role ownership (organization or global role), and requested permission.
