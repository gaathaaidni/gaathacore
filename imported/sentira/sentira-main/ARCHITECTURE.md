# Sentira AI Architecture

## Product Definition

Sentira AI is a multi-tenant AI visual intelligence platform built for operational monitoring across industries. It is not a simple CCTV viewer. It ingests camera streams, applies configurable rules, verifies AI detections with confidence thresholds, stores evidence, triggers notifications, and presents incidents in a business-oriented operational dashboard.

## Core design principles

- Multi-tenant by organization
- Industry-agnostic rule model
- AI provider abstraction
- Secure, role-based access controls
- Event-driven asynchronous processing
- Privacy-first retention and access policies
- Modular deployment for local demo and scaled production

## Product architecture

```text
[Frontend Web App]
        |
        v
[API Gateway / Core API]
        |
        +--> Auth Service
        +--> Organization / Site / User Service
        +--> Camera Management
        +--> Rule Engine
        +--> Event Service
        +--> Notification Service
        +--> Analytics / Reporting
        +--> Audit Logging
        |
        v
[Message Queue / Event Bus]
        |
        +--> AI Worker Pool
        +--> Video Processing Workers
        +--> Notification Workers
        +--> Reporting Workers
        |
        v
[Storage Layer]
  - Postgres (core data)
  - Redis (cache / sessions / pubsub)
  - MinIO / object storage (video, snapshots)
  - Blob store or specialized media storage

[Streaming Layer]
  - Media Gateway
  - WebRTC/HLS adapters
  - RTSP ingest
```

## Why this stack

For a production-ready SaaS platform with video, AI inference, WebSockets, and multi-tenancy, the recommended baseline is:

- Frontend: Next.js for a fast, enterprise dashboard and future mobile-ready API consumption
- Backend: NestJS for modular, secure, structured enterprise APIs
- Database: PostgreSQL for relational multi-tenant schema and auditability
- Cache / events: Redis for session caching and pub/sub
- Queue: RabbitMQ or Kafka-style async processing for AI and video tasks
- Object storage: MinIO for local development, S3-compatible storage for production
- Video streaming: media gateway with WebRTC/HLS to avoid directly exposing raw RTSP in browsers
- AI runtime: Python service or ONNX/TensorRT-compatible workers for video inference and model orchestration

This allows local development to run on moderate hardware while keeping GPU-heavy inference and video workloads scalable independently.

## Layer responsibilities

### 1. Frontend

Responsible for:
- Enterprise SaaS UI
- Live monitoring interface
- Dashboard, analytics, events, investigation pages
- Authentication and authorization state
- Real-time updates via WebSocket/SSE

### 2. Core API / Gateway

Responsible for:
- Request validation
- Multi-tenant scoping
- Role enforcement
- CRUD for Organizations, Sites, Cameras, Zones, Rules, Events
- WebSocket connection orchestration and API docs

### 3. Authentication and permissions

Responsible for:
- Login, JWT/session issuance
- role-based access checks
- audit trail for permission changes
- server-side enforcement of tenant isolation

### 4. Rule engine

Responsible for:
- user-defined conditions and actions
- temporal logic across objects, zones, and durations
- production of event triggers with confidence thresholds
- integration with AI detection results rather than model-specific logic

### 5. AI processing layer

Responsible for:
- model abstraction and provider interfaces
- frame sampling and inference scheduling
- object detection and tracking
- confidence scoring and event classification
- writing evidence metadata for downstream event pipelines

### 6. Video processing / stream gateway

Responsible for:
- RTSP ingest acquisition
- frame buffering and rolling evidence capture
- stream adaptation for browser-safe HLS/WebRTC
- connection monitoring and health checks

### 7. Event service

Responsible for:
- event lifecycle state transitions
- evidence association
- notifications
- dashboard updates
- escalation and resolution workflows

### 8. Notification service

Responsible for:
- in-app notifications
- email, webhook, push, future SMS/WhatsApp integrations
- quiet hours and escalation policies

## Industry → Rules → Cameras → Zones → Events → Actions model

Each organization can define:
- one or more industries
- templates or custom rule sets
- associated cameras and zones
- events and actions to trigger

This makes the product reusable across restaurants, warehouses, hospitals, retail, and factories with a common platform backbone.

## Deployment phases

### Phase 1
- 10–50 cameras
- local Postgres + Redis + RabbitMQ
- single AI worker pool
- local object storage

### Phase 2
- 100–500 cameras
- horizontal AI workers
- multiple stream gateways
- dedicated reporting workers
- enhanced HA for API and queue layers

### Phase 3
- 1,000+ cameras
- region-aware deployment
- clustered queue and storage
- GPU pools and model optimization
- event-driven data lake or analytics warehouse

## Key implementation constraints

- Do not expose RTSP credentials in frontend code
- Keep all permission checks server-side
- Treat AI output as evidence, not final human judgment
- Prefer asynchronous queues for expensive processing
- Build model abstraction before implementing business rules
- Keep media access signed and tenant-scoped

## Recommended code structure

```text
sentira/
  apps/
    api/
    web/
    ai-worker/
    stream-gateway/
  packages/
    shared/
  docker-compose.yml
  ARCHITECTURE.md
  DATABASE.md
  API.md
  SECURITY.md
  README.md
```

## Phase 5 additions

Phase 5 keeps the NestJS API, Next.js frontend, Python AI worker, and Stream Gateway architecture intact. The new production-intelligence layer introduces:

- `TrackingProvider` abstraction in the AI worker.
- Model-provider metadata abstraction for normalized model outputs.
- Generic rule definitions that compose triggers, conditions, temporal/spatial predicates, line crossings, counts, sequences, cooldowns, and actions.
- Action executor abstraction for asynchronous notifications and webhooks.
- WebRTC-first playback discovery with HLS fallback.
- Metrics counters for API and Stream Gateway observability.

## Phase 6 production-readiness additions

Phase 6 wires persisted advanced rule definitions into the API rule engine, adds TTL-scoped event deduplication and temporal state abstractions, introduces an asynchronous notification queue abstraction with retries/idempotency, hardens private evidence metadata, exposes authenticated system health, and updates the web dashboard with real-stream states rather than fake live video.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 8 control plane
The control plane remains NestJS + TypeORM. JWT access tokens identify organization scope; hashed refresh tokens are stored in `user_sessions`. Analytics uses database aggregation rather than loading events into application memory. Production schema evolution is migration-only.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C evidence boundary

The API validates normalized detection envelopes before tenant camera lookup and
rule evaluation. Evidence is read through an authenticated API route; browser
clients never receive MinIO credentials. Snapshot uploads carry SHA-256, byte
size, and content type metadata.

## Phase 10E runtime boundary

The API remains the sole holder of MinIO credentials and uses signed S3-compatible
bucket, object PUT/GET/HEAD/DELETE operations. The detection consumer remains the
single AMQP ingress and schedules one reconnect after a closed broker connection.
These are implementation details, not live integration evidence: Docker-backed
verification remains blocked as recorded in `PHASE_10E_COMPLETION_REPORT.md`.
