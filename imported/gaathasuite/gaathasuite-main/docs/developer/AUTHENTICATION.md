# Authentication

**Status:** IMPLEMENTED foundation / session lifecycle NOT FULLY VERIFIED.

The active API uses JWT access tokens, password hashing, inactive-account rejection, and refresh-cookie issuance. `get_current_user` resolves the token subject against username or email. WebSocket authentication uses a session cookie.

Refresh rotation, revocation, logout invalidation, password reset, and email verification are not verified as complete security workflows. Reproduce auth issues with a test account and never log credentials or tokens.
