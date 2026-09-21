# Capability Matrix

## Current status

Status: YELLOW

This matrix records the implementation state of the major product capabilities, based on actual repository evidence rather than aspirational roadmap claims.

| Capability | Status | Notes |
| --- | --- | --- |
| Authentication and basic tenant registration | YELLOW | Functional smoke tests exist |
| Dashboard stats | GREEN (limited) | Scoped by org in the active route |
| CRM | YELLOW | Basic create/update flows exist |
| Inventory | YELLOW | Stock adjustment and warehouse flows exist, but full validation is incomplete |
| Sales / invoicing | YELLOW | Invoice payment flows exist but not fully audited |
| Procurement / AP | YELLOW | Vendor and purchase-related models exist but not fully verified |
| HR | YELLOW | Model and route structure exists |
| Accounting | YELLOW | Core schema exists; posting and balance validation need proof |
| File import/export security | YELLOW | Token scoping exists; broad validation incomplete |
| Background workers | YELLOW | Config exists but operational proof is missing |
| Backup/restore | RED | Not rehearsed |
| Production operations | YELLOW | Config and health routes exist but not all deployment gates are proven |

## Release guidance

Do not treat any capability as green unless the route, permissions, and operational evidence are all present.
