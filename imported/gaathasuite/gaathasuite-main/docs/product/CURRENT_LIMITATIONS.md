# Current Limitations

**Status:** IMPLEMENTED as an audit register.  
**Last verified:** 2026-09-11

| Limitation | Impact | Area | Severity | Workaround / next step |
|---|---|---|---|---|
| Route-wide tenant isolation is not proven | Cross-tenant access cannot be ruled out for every route | FastAPI and legacy routes | BLOCKER for unrestricted production claims | Complete route-by-route read/update/delete tests |
| Permission matrix coverage is incomplete | Some role behavior may regress without detection | RBAC | HIGH | Add endpoint and role matrix tests |
| Legacy Flask modules remain | Duplicate behavior and maintenance risk | Architecture | HIGH | Keep legacy routes isolated while consolidating |
| Celery worker deployment is not evidenced | Background tasks may not execute in production | Jobs | HIGH | Define and verify a worker service |
| Upload security controls are incomplete | File type, size, malware, and storage controls need verification | Files | HIGH | Add validation, isolation, and security tests |
| Production backup/restore is not verified | Recovery time and data recovery are uncertain | Operations | HIGH | Perform documented restore drills |
| Legal seed content is placeholder text | It must not be relied on as final policy | Legal | HIGH | Replace only after legal review |
| No frontend test suite was found | UI regressions may escape CI | Frontend | MEDIUM | Add focused component and end-to-end tests |
| Data export/deletion workflows are not complete | Privacy requests require operator handling | Privacy | HIGH | Implement authorized workflows and retention rules |
