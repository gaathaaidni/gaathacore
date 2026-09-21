# Validation and Error Handling

**Status:** IMPLEMENTED foundation.

FastAPI/Pydantic request validation returns `422` with `VALIDATION_ERROR` and validation details. HTTP exceptions are normalized by the active application handler. Unexpected exceptions are logged server-side and returned as `INTERNAL_ERROR` with a generic message.

Route-specific messages and legacy Flask behavior are not yet uniform. Do not expose SQL, stack traces, file paths, secrets, or internal hostnames to customers.
