# Beta Release Criteria

**Status:** IMPLEMENTED gate; current status is PARTIALLY READY.

- **BLOCKER:** startup/database/authentication failure, cross-tenant access, critical authorization bypass, destructive corruption, or broken production build.
- **HIGH:** critical workflow failure, file-access vulnerability, missing important role restriction, unsafe migration, or unverified recovery for required data.
- **MEDIUM:** incomplete UX, documentation gap, or non-critical workflow issue.
- **LOW:** cosmetic, wording, or minor usability issue.

The repository should not be called beta-ready until blocker conditions are resolved and verified in the target environment.
