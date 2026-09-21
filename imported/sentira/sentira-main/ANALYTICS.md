# Analytics

## IMPLEMENTED — NOT VERIFIED
`/api/analytics/{overview,events,cameras,rules,sites,sla,alerts}` always derives organization scope from the authenticated token and uses SQL aggregation. Overview supports event filters and returns event totals, severity counts, acknowledgement/resolution/false-positive rates, and timing averages.
