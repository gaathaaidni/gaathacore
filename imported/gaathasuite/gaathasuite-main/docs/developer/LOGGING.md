# Logging

**Status:** PARTIALLY IMPLEMENTED.

The active app logs unhandled exceptions and readiness database failures. Technical details belong in operator-controlled logs, not API responses. Never log passwords, tokens, authentication headers, payment-card data, or secret values.

Structured request IDs, retention, centralized collection, and complete audit event coverage are not verified and should be designed before claiming operational observability.
