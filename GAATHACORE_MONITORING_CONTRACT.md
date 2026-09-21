# GaathaCore Staging Monitoring Contract

**Status:** Provider-neutral contract. Local Core checks are implemented; no external monitoring or alert destination is connected.

## Signal Contract

| Signal | Minimum observation | Alert condition | Local status |
|---|---|---|---|
| Service availability | Process/CLI invocation result | Expected operation cannot start | Core CLI available; no daemon probe |
| PostgreSQL connectivity | Core `SELECT 1` and database identity | Connection fails or identity is unexpected | Implemented by Core health/identity commands |
| Migration pending state | Migration head and pending list | Pending migrations outside an approved change | Implemented by Core status/health |
| Readiness | Configuration, DB, migration, and schema state | Core reports `not_ready` | Implemented by `core_health()` and CLI exit code |
| Backup failure | Dump exit status, non-empty artifact, archive listing | Any step fails | Implemented locally for Core backup; no scheduler |
| Restore failure | Disposable restore exit status and post-restore health | Restore or verification fails | Guarded local Core workflow; no alert sink |
| Queue failure | Broker reachability, queue depth, consumer/retry state | Product-specific threshold breach | Designed only; no Core queue |
| Excessive errors | Sanitized application error counts/rates | Approved product threshold breach | Designed only |
| Disk/storage concern | Database/filesystem/object-storage capacity | Approved utilization threshold breach | Designed only |
| Authentication/security failure | Invalid auth spikes, secret/config errors, access-denied anomalies | Approved threshold or confirmed incident | Designed only |

## Event Fields

A future provider adapter should carry: `event_name`, `severity`, `service`, `environment`, UTC timestamp, sanitized description, correlation/change identifier, database identity where relevant, owner `[TBD]`, and remediation state. It must not carry passwords, tokens, connection URLs, stack traces, or customer data.

## Severity and Handling

- `INFO`: expected state or completed verification.
- `WARNING`: degraded or pending state requiring owner review.
- `CRITICAL`: failed readiness, backup, restore, database identity check, or security control requiring immediate staging stop/escalation.

Alert routing, acknowledgement, escalation timing, and notification provider remain `[TBD]`. No fake alerts are emitted by this repository.

## Local Verification

The executable local checks are:

```text
python -m core.operations_cli identity
python -m core.operations_cli status
python -m core.operations_cli health
scripts/core_staging.sh backup
scripts/core_staging.sh restore
```

The CLI returns non-zero for non-ready health and pending status. PostgreSQL errors are summarized without connection details. Backup integrity is checked before success is reported.

## Explicit Boundary

This contract does not install Prometheus, Grafana, Sentry, CloudWatch, PagerDuty, email, or any other external monitoring service. Product queues, workers, object storage, and application endpoints remain product-owned and require product-specific probes before they can be included as implemented signals.
