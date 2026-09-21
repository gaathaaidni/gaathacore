# Backup and Restore Verification

## Status

RED

This procedure has not been rehearsed in a controlled environment and therefore cannot be claimed as production-verified.

## Required process

1. Create a PostgreSQL logical or physical backup from a disposable database clone.
2. Restore into a temporary database environment.
3. Run migrations against the restored database.
4. Verify schema parity.
5. Validate row counts and critical relationships.
6. Test application startup with the restored database.
7. Confirm health and readiness routes pass.
8. Record the results in the release log.

## Safety guardrails

- Never restore over the live production database.
- Use a disposable database or isolated environment.
- Confirm credentials are not hardcoded or logged.
- Keep backup files outside the application working tree when possible.

## Next action

Perform a controlled backup/restore rehearsal in a staging or disposable environment before calling the release operationally ready.
