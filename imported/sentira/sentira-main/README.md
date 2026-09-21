
# Sentira AI

## Product Name

Sentira AI

## Core Tagline

The Intelligent Eye for Every Operation.

## Developer

Hardikkumar Gajjar

## Company

Gaatha Ventures

## Executive Summary

Sentira AI is an AI-powered visual intelligence platform for operational monitoring, incident detection, and evidence-based investigation. It is designed to work across multiple industries and provide real-time awareness without requiring operators to monitor dozens of screens manually.

## Vision

Cameras watch. Sentira understands. Sentira alerts. Humans decide.

## Repository Status

This repository contains a production-ready enterprise architecture with:

- Modular monorepo structure
- TypeORM database models with multi-tenancy support
- NestJS API with authentication and role-based access control
- Complete domain models for organizations, cameras, rules, zones, events
- Authentication with JWT
- Tenant isolation via organization scoping
- TypeScript throughout for type safety

## What's implemented

### Backend (API - Phase 1 Complete)

✅ Database entities and TypeORM configuration
✅ Multi-tenant organization/site/camera model
✅ JWT authentication with NestJS Passport
✅ Role-based access control (RBAC)
✅ Core services: organizations, cameras, zones, rules, events
✅ API endpoints with tenant scoping
✅ Audit logging entities
✅ Event generator service for demo/testing
✅ Rule engine with confidence thresholds and scheduling
✅ Notification service with multi-channel support
✅ Demo API endpoints for sales demonstrations
✅ Complete test suite (all passing)
✅ **Phase 2: WebSocket Gateway for real-time events**

### Frontend (Next.js - Phase 2 In Progress)

- **Phase 2: Full-featured dashboard, event management, and real-time updates.**

### Infrastructure

- Docker Compose for local development (PostgreSQL, Redis, RabbitMQ, MinIO)

## API endpoints

All endpoints except `/api/auth/login` require `Authorization: Bearer <token>` header.

### Authentication

- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current authenticated user

### Organizations & Sites

- `GET /api/organizations/:id` - Get organization
- `GET /api/organizations/:id/sites` - List sites
- `POST /api/organizations/:id/sites` - Create site

### Cameras

- `GET /api/cameras` - List cameras in organization
- `GET /api/cameras/:id` - Get camera details
- `POST /api/cameras` - Add camera
- `GET /api/cameras/site/:siteId` - Get cameras by site

### Events

- `GET /api/events` - List events
- `GET /api/events/:id` - Get event details
- `POST /api/events/:id/acknowledge` - Acknowledge event
- `POST /api/events/:id/resolve` - Resolve event
- `POST /api/events/:id/dismiss` - Dismiss event

### Rules

- `GET /api/rules` - List rules
- `GET /api/rules/:id` - Get rule details
- `POST /api/rules` - Create rule

### Zones

- `GET /api/zones/:id` - Get zone
- `GET /api/zones/camera/:cameraId` - Get zones by camera
- `POST /api/zones` - Create zone

### Demo & Testing

- `POST /api/demo/generate-event` - Create single demo event from rule
- `POST /api/demo/trigger-all-rules` - Batch trigger all rules (70% probability)
- `GET /api/demo/dashboard-data` - Get mock dashboard stats with demo flag

## Architecture

This is a modular monorepo using:

- **Frontend**: Next.js 14 (React 18) + TypeScript
- **API**: NestJS 11 + TypeORM + PostgreSQL
- **Auth**: JWT + Passport
- **Storage**: MinIO (S3-compatible) for media
- **Queue**: RabbitMQ for async tasks
- **Cache**: Redis for sessions and pub/sub

### Project structure

```
sentira/
  apps/
    api/          # NestJS backend
    web/          # Next.js frontend
    ai-worker/    # Python/GPU inference (planned)
    stream-gateway/  # RTSP/WebRTC gateway (planned)
  packages/
    shared/       # Shared types and utilities
  docker-compose.yml
  ARCHITECTURE.md
  DATABASE.md
  API.md
  SECURITY.md
  RULE_ENGINE.md
  AI_PIPELINE.md
  DEMO.md
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and multi-layer architecture
- [DATABASE.md](DATABASE.md) - Schema, entities, and data model
- [API.md](API.md) - REST API contract and conventions
- [SECURITY.md](SECURITY.md) - Security model, encryption, compliance
- [RULE_ENGINE.md](RULE_ENGINE.md) - Rule definition language and execution
- [AI_PIPELINE.md](AI_PIPELINE.md) - AI detection, model abstraction, and workers
- [DEMO.md](DEMO.md) - Demo mode and simulated event generation

## Phase 10F production-gate status

Phase 10F locks the AMQP client and declarations, removes unresolved Compose
conflict markers, and adds dependency-health classification coverage. Local
TypeScript and Python checks pass. Docker image export and the cross-service
runtime gate remain pending; see `PHASE_10F_COMPLETION_REPORT.md`.

## Development practices

## Phase 10G runtime status

The complete Compose stack, clean migration cycle, deterministic RTSP pipeline,
snapshot retrieval, and refresh replay rejection were verified live. Evidence clip
orchestration, dependency probes, and full tenant/WebSocket E2E remain blockers.

### Testing

```bash
npm test          # Run all tests
npm --workspace apps/api run test
```

### Linting

```bash
npm run lint      # Lint all workspaces
```

### Building

```bash
npm run build     # Build all workspaces
npm --workspace apps/api run build
npm --workspace apps/web run build
```

## Demo credentials

```
Email:    demo@example.com
Password: demo_password
```

## Environment variables

The API intentionally refuses to start without `CAMERA_CREDENTIAL_ENCRYPTION_KEY`, because
using an ephemeral or default key would make persisted camera credentials unreadable and weaken
their encryption. Create a local configuration file before starting the API:

```bash
cp .env.example .env.local
openssl rand -base64 48
```

Set the generated value as `CAMERA_CREDENTIAL_ENCRYPTION_KEY` in `.env.local`. Also replace
`JWT_SECRET` and `STREAM_GATEWAY_INTERNAL_TOKEN` with unique values; the latter must match the
Stream Gateway configuration.

For local integration testing, `docker-compose up` supplies development-only fallback values for
these three secrets, so it can start without a local environment file. Never use those fallback
values in a shared or production environment; set all three variables explicitly instead.

```dotenv
NODE_ENV=development
API_PORT=4000
DB_HOST=localhost
DB_PORT=5432
DB_USER=sentira
DB_PASSWORD=sentira_dev_password
DB_NAME=sentira
JWT_SECRET=replace-with-a-unique-jwt-signing-secret
STREAM_GATEWAY_INTERNAL_TOKEN=replace-with-a-unique-stream-gateway-token
CAMERA_CREDENTIAL_ENCRYPTION_KEY=replace-with-a-random-secret-of-at-least-32-characters
```

## What's next

- [x] **Phase 1 Complete:** Backend foundation, multi-tenancy, auth, and demo pipeline.
- [x] **Phase 2 In Progress:** WebSocket gateway, real-time dashboard, event management UI.
- [ ] Database migrations
- [ ] Video evidence capture and storage
- [ ] Frontend dashboard completion
- [ ] Advanced rule engine temporal logic
- [ ] Actual AI model integration

## Attribution

Built by **Hardikkumar Gajjar** under **Gaatha Ventures**.

## Phase 5 production intelligence additions

Phase 5 adds an incremental enterprise-intelligence layer without replacing the existing architecture:

- Advanced tracking abstraction in the AI worker with bounded lightweight IoU tracking.
- Generic Phase 5 rule evaluator for compound conditions, duration, line crossing, counting, and sequences.
- WebRTC-ready Stream Gateway playback discovery with HLS fallback.
- Event-intelligence schema migration for track IDs, model metadata, evidence status, and detection time ranges.
- Configuration-driven industry rule templates with explicit model capability requirements.
- Observability and performance documentation that does not invent benchmark results.

See `PHASE5_COMPLETION_REPORT.md` for implementation status and limitations.

## Phase 6 production readiness

Phase 6 adds persisted advanced rules, stateful TTL tracking, distributed-safe deduplication keys, asynchronous notifications, authenticated system health, private evidence metadata, MediaMTX/WebRTC-oriented stream metadata, and a live monitor UI that clearly distinguishes online, connecting, offline, and unavailable streams.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 8 status
PARTIALLY IMPLEMENTED: authenticated refresh-token sessions, tenant-scoped analytics, CSV export, event lifecycle auditing, correlation IDs, RBAC guard, and operational UI foundations are available. Durable escalation/SLA/retention workers are not yet implemented; see `PHASE_8_COMPLETION_REPORT.md`.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration environment

Phase 10B adds the local Compose topology (`postgres`, `redis`, `rabbitmq`, `minio`,
`mediamtx`, `api`, `web`, `ai-worker`, and `stream-gateway`). The deterministic
AI provider is intentionally integration-only and publishes a normalized detection
to the durable `detection.queue`. The Stream Gateway now uses FFmpeg to extract
JPEG frames and create bounded per-camera rolling MP4 segments. See
`PHASE_10B_COMPLETION_REPORT.md` for the exact verified and unverified scope.

## Phase 10C integration status

Phase 10C adds API detection-envelope validation and rule/event orchestration, an
API-authorized evidence read endpoint, integrity metadata, and the deterministic
MediaMTX fixture publisher. Evidence object keys are tenant scoped and object
storage credentials remain server-side. See `PHASE_10C_COMPLETION_REPORT.md` for
runtime verification limits and the fixture command.

## Phase 10D verification status

Phase 10D declares the production AMQP client (`amqplib`) and strengthens the
single API detection consumer with durable topology, bounded retry, DLQ routing,
correlation propagation, reconnect scheduling, and shutdown handling. The
execution environment returned HTTP 403 for the package download and has no
Docker binary, so the lockfile/image installation and live Compose golden path
remain unverified. See `PHASE_10D_COMPLETION_REPORT.md` for an explicit status
of every runtime dependency; deterministic AI inference remains integration-only.

## Phase 10E verification status

Phase 10E is **partially verified and not production ready**. The API storage adapter
now has signed S3-compatible bucket/PUT/GET/HEAD/DELETE operations and the AMQP
consumer has graceful reconnect handling, but AMQP package installation was blocked
by an npm HTTP 403 response and Docker is unavailable in the verification environment.
No Compose, migration, RabbitMQ, Redis, MinIO, RTSP/FFmpeg, WebSocket, or two-tenant
runtime result is claimed. See `PHASE_10E_COMPLETION_REPORT.md` for exact commands
and blocked checks.
