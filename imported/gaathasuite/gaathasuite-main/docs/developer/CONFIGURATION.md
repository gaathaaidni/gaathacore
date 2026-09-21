# Configuration Reference

**Status:** IMPLEMENTED from current configuration files; production values are not included.

| Variable | Purpose | Required | Secret | Notes |
|---|---|---:|---:|---|
| `SECRET_KEY` | JWT/signing and application security | Yes | Yes | No committed or fallback production value |
| `DATABASE_URL` | PostgreSQL connection | Yes | Yes | Async SQLAlchemy URL |
| `TEST_DATABASE_URL` | Isolated test database | Tests | Yes | Used by backend tests |
| `REDIS_URL` | Redis integrations and task/rate-limit configuration | Optional in some paths | Often | Runtime worker behavior is not fully verified |
| `APP_ENV` | Environment selection | No | No | Production enables secure cookies |
| `CORS_ORIGINS` | Allowed browser origins | Production | No | Comma-separated; wildcard is not default |
| `BASE_URL` | Absolute links for downloads/reset flows | Deployment | No | Must match public origin |
| `JWT_EXPIRE_MINUTES` | Access-token lifetime override | No | No | Default is 24 hours in config |
| `SUPERADMIN_EMAIL` / `SUPERADMIN_PASSWORD` | Initial administrative setup | Deployment-dependent | Password yes | Rotate and protect; do not publish |
| `SMTP_*`, `MAIL_*`, `RESEND_API_KEY` | Email delivery | Optional | Yes | Provider behavior depends on configured values |
| `GOOGLE_*`, `MICROSOFT_*` | OAuth credentials | Optional | Yes | Do not claim provider login unless configured and tested |
| `GROQ_API_KEY`, `GROQ_MODEL` | AI assistant provider | Optional | Key yes | AI authorization and tenancy need review |
| `CASHFREE_*`, `PAYMENT_PROVIDER` | Payment integration settings | Optional | Client secret yes | Webhook verification is not yet verified |
| `COMPANY_*` | Company display defaults | Optional | Usually no | Not the confirmed legal identity |

Environment templates are `backend/.env.example` and `.env.example`. Never copy example secrets into production.
