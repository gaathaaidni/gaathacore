# Security Foundation

## Implemented in Phase 2

- Required `DATABASE_URL` and `SECRET_KEY` configuration; no generated or hardcoded runtime secret fallback.
- Production cookie security follows `APP_ENV=production`.
- Inactive authenticated accounts are rejected.
- Organization admins cannot assign the `superadmin` role.
- FastAPI returns structured safe errors for HTTP, validation, and unhandled exceptions.
- Security response headers include content-type sniffing, framing, and referrer protections.
- CORS origins are opt-in through `CORS_ORIGINS`; wildcard origins are not enabled by default.

## Not verified

- Full route-by-route authorization and tenant isolation.
- Refresh-token rotation/revocation and logout semantics.
- Rate limiting, password reset, email verification, file-upload security, webhook verification, and dependency scanning.
- Production HTTPS and proxy configuration.

Secrets must be provided through deployment configuration. They must not be placed in Compose files, source code, logs, or committed environment files.
