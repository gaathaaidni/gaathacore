# Sentira AI Rule Engine

## Purpose

The rule engine is the core of Sentira AI. It translates business conditions into event triggers while remaining model-agnostic and industry-neutral.

## Rule model

A rule is composed of:
- metadata
- conditions
- actions
- schedule
- confidence threshold
- severity

## Example rule structure

```json
{
  "name": "Table unattended",
  "industry": "restaurant",
  "conditions": [
    {
      "type": "presence",
      "object": "person",
      "zone": "table_12",
      "operator": "exists_for",
      "value": 120
    },
    {
      "type": "absence",
      "object": "employee",
      "zone": "table_12",
      "operator": "not_present_for",
      "value": 120
    }
  ],
  "actions": [
    { "type": "create_event", "severity": "medium" },
    { "type": "save_video_clip", "pre_event_seconds": 10, "post_event_seconds": 10 },
    { "type": "notify", "channel": "in_app" }
  ],
  "confidence_threshold": 0.8,
  "schedule": {
    "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "start": "09:00",
    "end": "22:00"
  }
}
```

## Supported condition types

- object type
- camera
- zone
- time window
- duration
- count
- direction
- presence
- absence
- entry
- exit
- loitering
- proximity/distance
- sequence of events
- confidence threshold
- schedule

## Supported action types

- create event
- save video clip
- send notification
- send email
- send push notification
- webhook
- escalate
- create task

## Rule engine flow

```text
Detection stream
  -> normalization
  -> temporal aggregation
  -> rule matching
  -> confidence evaluation
  -> event creation
  -> evidence capture
  -> notification dispatch
```

## Design responsibility

The rule engine must not contain model-specific logic. It should interpret generic AI outputs such as:
- object_types
- tracks
- bounding boxes
- zone occupancy
- timestamps
- confidence scores

This ensures the same rule language can be used across YOLO, RT-DETR, or custom models.

## Phase 6 persisted advanced rules

Advanced rules are persisted in `rules.definition_json` and can combine object detection, confidence thresholds, zone entry/exit, duration, count, absence, sequence, schedule, cooldown, severity, and actions. Distributed deployments use deterministic keys shaped like `sentira:event:{organizationId}:{cameraId}:{ruleId}:{trackingKey}` for deduplication and `sentira:rule-state:{organizationId}:{cameraId}:{ruleId}:{trackingKey}` for temporal state.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.
