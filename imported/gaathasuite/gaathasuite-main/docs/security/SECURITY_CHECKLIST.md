# Security Checklist

**Status:** RELEASE CHECKLIST / NOT ALL ITEMS VERIFIED.

- Secrets supplied outside source control
- PostgreSQL and Redis private
- TLS and proxy headers verified
- CORS origins explicit
- Authentication and inactive-account tests pass
- Negative RBAC and tenant tests pass
- Upload/download traversal and ownership tests pass
- Webhook signatures and idempotency verified if payments enabled
- Logs redact secrets and personal data
- Backup restore drill completed
- Dependencies reviewed
- Rollback owner and recovery plan recorded
