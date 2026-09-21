# Sentira AI Database Schema

## Overview

Phase 10G executed the clean migration down/up cycle against PostgreSQL and verified
core tables plus EventMedia integrity columns after re-application.

The platform uses PostgreSQL as the core transactional database. Every tenant-scoped entity must include organization_id to enforce data isolation.

## Core entities

### organizations
- id (UUID, PK)
- name
- legal_name
- status
- created_at
- updated_at

### sites
- id (UUID, PK)
- organization_id (UUID, FK)
- name
- address
- timezone
- status
- created_at
- updated_at

### users
- id (UUID, PK)
- organization_id (UUID, FK)
- email
- password_hash
- first_name
- last_name
- role_id (UUID, FK)
- status
- last_login_at
- created_at
- updated_at

### roles
- id (UUID, PK)
- organization_id (UUID, FK, nullable for global)
- name
- description
- created_at
- updated_at

### permissions
- id (UUID, PK)
- role_id (UUID, FK)
- resource
- action
- created_at

### cameras
- id (UUID, PK)
- organization_id (UUID, FK)
- site_id (UUID, FK)
- camera_group_id (UUID, FK, nullable)
- name
- location
- stream_url_encrypted
- protocol
- status
- resolution
- fps
- last_heartbeat_at
- ai_processing_status
- is_enabled
- created_at
- updated_at

### camera_groups
- id (UUID, PK)
- organization_id (UUID, FK)
- site_id (UUID, FK)
- name
- description
- created_at
- updated_at

### zones
- id (UUID, PK)
- organization_id (UUID, FK)
- camera_id (UUID, FK)
- name
- zone_type
- geometry_json
- coordinates_json
- is_enabled
- created_at
- updated_at

### rules
- id (UUID, PK)
- organization_id (UUID, FK)
- site_id (UUID, FK, nullable)
- camera_id (UUID, FK, nullable)
- name
- description
- rule_type
- status
- schedule_json
- confidence_threshold
- is_active
- created_by
- created_at
- updated_at

### rule_conditions
- id (UUID, PK)
- rule_id (UUID, FK)
- condition_type
- field_name
- operator
- value_json
- sequence_order
- created_at

### rule_actions
- id (UUID, PK)
- rule_id (UUID, FK)
- action_type
- config_json
- created_at

### ai_models
- id (UUID, PK)
- organization_id (UUID, FK, nullable)
- name
- provider
- version
- model_type
- status
- config_json
- created_at
- updated_at

### detections
- id (UUID, PK)
- organization_id (UUID, FK)
- event_id (UUID, FK)
- camera_id (UUID, FK)
- model_id (UUID, FK)
- object_type
- confidence
- bbox_json
- track_id
- timestamp
- created_at

### events
- id (UUID, PK)
- organization_id (UUID, FK)
- site_id (UUID, FK)
- camera_id (UUID, FK)
- rule_id (UUID, FK)
- event_type
- severity
- status
- confidence
- description
- duration_seconds
- zone_id (UUID, FK, nullable)
- assigned_user_id (UUID, FK, nullable)
- acknowledged_by_user_id (UUID, FK, nullable)
- resolved_by_user_id (UUID, FK, nullable)
- snapshot_url
- video_clip_url
- notes
- created_at
- updated_at

### event_media
- id (UUID, PK)
- event_id (UUID, FK)
- media_type
- storage_url
- width
- height
- duration_seconds
- created_at

### notifications
- id (UUID, PK)
- organization_id (UUID, FK)
- event_id (UUID, FK, nullable)
- user_id (UUID, FK, nullable)
- channel
- priority
- status
- sent_at
- payload_json
- created_at

### notification_rules
- id (UUID, PK)
- organization_id (UUID, FK)
- rule_id (UUID, FK)
- user_id (UUID, FK)
- channel
- priority
- quiet_hours_json
- escalation_rule_json
- created_at

### audit_logs
- id (UUID, PK)
- organization_id (UUID, FK)
- user_id (UUID, FK, nullable)
- action
- resource_type
- resource_id
- ip_address
- previous_value_json
- new_value_json
- created_at

### subscriptions
- id (UUID, PK)
- organization_id (UUID, FK)
- plan_name
- status
- seats
- camera_limit
- storage_limit
- created_at
- updated_at

### usage_metrics
- id (UUID, PK)
- organization_id (UUID, FK)
- site_id (UUID, FK, nullable)
- camera_id (UUID, FK, nullable)
- metric_type
- value_numeric
- recorded_at
- created_at

## Index recommendations

Important indexes:
- organization_id
- site_id
- camera_id
- timestamp or created_at
- event_type
- status
- severity
- user_id
- rule_id
- resource_id

## Example indexes

```sql
CREATE INDEX idx_events_org_site_camera ON events(organization_id, site_id, camera_id);
CREATE INDEX idx_events_status_severity ON events(status, severity);
CREATE INDEX idx_events_type_timestamp ON events(event_type, created_at);
CREATE INDEX idx_detections_event_camera ON detections(event_id, camera_id);
CREATE INDEX idx_audit_logs_org_created ON audit_logs(organization_id, created_at);
CREATE INDEX idx_cameras_org_site ON cameras(organization_id, site_id);
```

## Retention policy

Retention is configured per organization and by media type. Recommended default values:
- 7 days
- 30 days
- 60 days
- 90 days
- custom

Media cleanup should be automated and auditable.

## Security notes

- Secret fields must be encrypted at rest
- Stream URLs or credentials must never be stored in plain text in frontend code
- Use organization_id and role checks in every data query
- Audit immutable actions such as permission changes, downloads, or event resolution

## Phase 6 migrations and retention

Production uses TypeORM migrations with `synchronize=false`. Phase 6 adds persisted advanced rule definitions (`definition_json`), severity, duplicate windows, cooldown seconds, rule versioning, and tenant-scoped private evidence metadata. Retention is configured with `EVENT_RETENTION_DAYS`, `VIDEO_RETENTION_DAYS`, `SNAPSHOT_RETENTION_DAYS`, and `AUDIT_LOG_RETENTION_DAYS`.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 8 migration safety — IMPLEMENTED, NOT VERIFIED
Production TypeORM configuration uses `synchronize: false` and `migrationsRun: true`. Run migrations through the deployed API migration process; review generated SQL and back up first. The Phase 8 migration is reversible only for its session table/index; event columns are retained on rollback to avoid destructive data loss.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C evidence integrity migration

Migration `1800000004000-Phase10CEvidenceIntegrity` adds `event_media.sha256`,
`byteSize`, and `contentType`, plus an organization/event index. It is reversible
and TypeORM synchronization remains disabled.

## Phase 10E migration verification

TypeORM migrations continue to run with `synchronize: false`. Clean PostgreSQL
`up -> verify -> down -> verify -> up -> verify` execution is still required and
was blocked in Phase 10E because Docker was unavailable. It must not be inferred
from migration source inspection.
