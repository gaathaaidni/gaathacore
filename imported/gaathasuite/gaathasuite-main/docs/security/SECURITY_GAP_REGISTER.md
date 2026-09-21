# Security Gap Register

**Status:** IMPLEMENTED as a register; items require remediation and verification.

| Gap | Evidence | Risk | Next action |
|---|---|---|---|
| Full tenant isolation is unverified | Existing docs and tests cover dashboard scoping only | Cross-tenant disclosure | Add route-by-route IDOR tests |
| Full RBAC matrix is unverified | Role dependencies exist, but coverage is incomplete | Unauthorized actions | Test every protected resource and mutation |
| Upload controls are not fully established | Upload folder exists; complete type/size/scanning controls are not evidenced | Malicious or unsafe files | Define and test upload policy |
| Refresh-token rotation/revocation is not verified | JWT refresh configuration exists | Session persistence after compromise | Implement and test rotation/revocation |
| Rate limiting is not production-proven | Redis dependency returns `None`; in-memory behavior exists | Brute force/abuse exposure | Provide shared Redis limiter and tests |
| Webhook signature/idempotency is not verified | Payment configuration exists | Payment state integrity | Verify provider callbacks before enabling production payments |
| Audit event coverage is incomplete | Activity log code exists | Weak investigation trail | Define required event taxonomy and coverage tests |
| HTTPS/proxy deployment is not runtime-verified | Nginx configuration exists | Transport/configuration risk | Validate certificates and proxy behavior in staging |

This register is not a penetration-test report and does not claim that every listed item is exploitable.
