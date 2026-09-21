# Sentira AI - Phase 4 Completion Report

**Date:** August 17, 2026
**Status:** Phase 4 Complete
**Objective:** Implement Real CCTV / RTSP Streaming, Stream Gateway, Rolling Buffer, and Evidence Clips.

---

## 1. Executive Summary

Phase 4 has successfully transformed Sentira AI from a demo-based system into a production-ready, real-time visual intelligence platform. The core achievement of this phase was the implementation of an end-to-end video pipeline capable of ingesting live RTSP streams from CCTV cameras, performing AI inference, and generating evidence-backed events.

A new, independent **Stream Gateway** service was created to manage all aspects of video ingestion, including robust connection handling, frame sampling, and a rolling buffer for pre-event evidence capture. The **AI Worker** was enhanced to process these live frames, and the **NestJS API** was upgraded with stateful temporal rule tracking and a secure, asynchronous evidence generation workflow.

Key security enhancements, such as at-rest encryption for camera credentials and the move to a production-safe database migration strategy, have been implemented. The frontend now supports live video playback and provides a rich interface for evidence investigation.

The successful completion of Phase 4 marks a major milestone, making Sentira AI a true enterprise-grade CCTV monitoring solution.

---

## 2. Architecture After Phase 4

The system now operates on a scalable, multi-service architecture:

```
REAL CCTV CAMERA
       │
       │ RTSP
       ▼
┌───────────────────┐
│   STREAM GATEWAY  │ (Python, FFmpeg)
│ - Connects to RTSP streams
│ - Manages rolling buffer
│ - Samples frames for AI
│ - Generates evidence clips
└─────────┬─────────┘
          │
┌─────────┴─────────┐
│ Redis             │ │ RabbitMQ
▼                   ▼
AI Frames      Evidence Jobs
│                   │
▼                   │
┌───────────────────┐   │
│     AI WORKER     │   │
│ - Consumes frames   │
│ - YOLO Inference    │   │
└─────────┬─────────┘   │
          │             │
          ▼             │
┌───────────────────┐   │
│     RabbitMQ      │   │
│ - `detection.queue` │   │
└─────────┬─────────┘   │
          │             │
          ▼             │
┌───────────────────┐   │
│    SENTIRA API    │   │
│ - Rule Engine       │   │
│ - Stateful Tracking │   │
│ - Triggers Evidence │───┘
└─────────┬─────────┘
          │
┌─────────┴─────────┐
│ WebSocket         │ │ MinIO
▼                   ▼
Real-time Alerts   Evidence Clips
│                   │
▼                   ▼
┌───────────────────┐
│  SENTIRA FRONTEND │
│ - Live Video (WebRTC/HLS)
│ - Evidence Playback
└───────────────────┘
```

---

## 3. Files Created

### Stream Gateway (`apps/stream-gateway`)
- `apps/stream-gateway/main.py`: FastAPI entry point with stream control endpoints.
- `apps/stream-gateway/camera_manager.py`: Manages the lifecycle of all camera stream subprocesses.
- `apps/stream-gateway/stream_process.py`: Core logic for a single camera's FFmpeg process, including reconnection and health monitoring.
- `apps/stream-gateway/rolling_buffer.py`: Manages the disk-based rolling buffer of video segments.
- `apps/stream-gateway/frame_publisher.py`: Samples frames and publishes them to Redis for the AI Worker.
- `apps/stream-gateway/evidence.py`: Handles evidence clip generation requests from RabbitMQ.
- `apps/stream-gateway/config.py`: Centralized environment configuration.

### Backend API (`apps/api`)
- `apps/api/src/modules/common/encryption.service.ts`: Service for AES-256-GCM encryption.
- `apps/api/src/modules/common/common.module.ts`: Shared module for common services.
- `apps/api/src/services/detection-state.service.ts`: Manages object tracking state in Redis for temporal rules.
- `apps/api/src/database/migrations/*`: Initial TypeORM database migration file.

### Documentation
- `docs/STREAMING.md`, `docs/VIDEO_PIPELINE.md`, `docs/CAMERA_SETUP.md`

---

## 4. Files Modified

### Root
- `docker-compose.yml`: Added the `stream-gateway` service and configured inter-service dependencies.

### Backend API (`apps/api`)
- `app.module.ts`: Imported and configured new modules and services.
- `cameras.service.ts`: Integrated `EncryptionService` for password handling.
- `cameras.controller.ts`: Added internal endpoints for the Stream Gateway.
- `rule-engine.service.ts`: Integrated `DetectionStateService` to evaluate `duration` rules.
- `event-generator.service.ts`: Modified to dispatch evidence capture jobs to RabbitMQ.
- `database.config.ts`: Disabled `synchronize: true` for production environments.

### AI Worker (`apps/ai-worker`)
- `main.py`: Added "live" mode to consume frames from Redis instead of a local video file.

### Frontend (`apps/web`)
- `live-monitor/page.tsx`: Replaced placeholder with a real video player component (HLS/WebRTC).
- `events/[id]/page.tsx`: Integrated a video player for evidence clip playback using secure, signed URLs.

---

## 5. Key Implementations

### 5.1. Stream Gateway & RTSP Ingestion
- **Real RTSP Connection:** The Stream Gateway now uses FFmpeg to connect to and decode real RTSP streams, with automatic reconnection logic using exponential backoff.
- **AI Frame Pipeline:** Frames are sampled at a configurable rate (`AI_FRAME_RATE`), encoded as JPEGs, and published to camera-specific Redis Streams for consumption by the AI Worker.

### 5.2. Rolling Buffer & Evidence Pipeline
- **Disk-Based Buffer:** The Stream Gateway maintains a bounded, rolling buffer of short video segments for each camera, retaining footage from before an event occurs.
- **Asynchronous Evidence Jobs:** When a rule is triggered, the API dispatches an `evidence.requested` job to a RabbitMQ queue.
- **Clip Generation:** The Stream Gateway consumes this job, uses FFmpeg to stitch segments from the rolling buffer into a complete `evidence.mp4` clip, and uploads it directly to MinIO.
- **Completion Notification:** Upon successful upload, the gateway notifies the API, which updates the `EventMedia` record and broadcasts an `evidence.ready` event via WebSocket.

### 5.3. Rule Engine & State Management
- **Stateful Temporal Tracking:** The new `DetectionStateService` uses Redis to track objects across frames, enabling the `RuleEngineService` to accurately evaluate `duration`-based rules (e.g., "person in zone for > 30 seconds").

### 5.4. Security Hardening
- **Credential Encryption:** All camera RTSP passwords are now encrypted at rest in the database using AES-256-GCM. The `EncryptionService` handles all encryption and decryption, and credentials are never exposed to the frontend or logs.
- **Secure Evidence Access:** The API now generates short-lived, signed URLs for accessing evidence clips from MinIO, preventing direct, unauthorized access.
- **Internal Service Authentication:** Communication between the API and Stream Gateway is secured with a shared internal token (`STREAM_GATEWAY_INTERNAL_TOKEN`).

### 5.5. Database Production-Readiness
- **Migrations Implemented:** The API has been transitioned from `synchronize: true` to a production-safe TypeORM migration strategy. An initial migration file has been generated, and scripts for `migration:generate` and `migration:run` are available.

---

## 6. Verification & Testing

### 6.1. Automated Tests
- **Unit Tests:** Added for the `EncryptionService` and `DetectionStateService`.
- **Build/Lint/Test Commands:**
  ```bash
  npm install
  npm run lint
  npm run test
  npm run build
  ```
- **Results:**
  - **Lint:** ✅ Passed with zero errors.
  - **Unit Tests:** ✅ All tests passed.
  - **Build:** ✅ Succeeded for all applications (`api`, `web`, `stream-gateway`, `ai-worker`).

### 6.2. End-to-End (E2E) Verification
- **Demo Mode:** The existing demo pipeline (`PIPELINE_MODE=demo`) remains fully functional.
- **Live Mode:** A full E2E test was conducted using a public RTSP test stream. The test successfully verified the entire pipeline:
  1. Stream Gateway connected to the RTSP stream.
  2. AI Worker received frames via Redis and published detections to RabbitMQ.
  3. Rule Engine matched a `person_detected` rule and triggered an event.
  4. An evidence capture job was dispatched and consumed.
  5. A 20-second `evidence.mp4` clip (10s pre-event + 10s post-event) was generated from the rolling buffer and uploaded to MinIO.
  6. The frontend received the `event.created` and `evidence.ready` WebSocket events and successfully played back the evidence clip using a signed URL.

---

## 7. Known Limitations

- **Live Video in UI:** The frontend live monitor uses HLS for broad compatibility. While functional, a direct WebRTC implementation would offer lower latency and is recommended for a future phase.
- **Object Tracking:** The temporal rule tracking is based on centroid proximity. Integrating a more advanced algorithm like ByteTrack would improve tracking robustness across object occlusions.
- **Scalability:** While the architecture is scalable, performance testing with a high volume of cameras (50+) has not been conducted.

---

## 8. Exact Commands to Run the System

1.  **Set Environment Variables:** Copy `.env.example` to `.env.local` and fill in all required values, especially `CAMERA_CREDENTIAL_ENCRYPTION_KEY`.

2.  **Start Infrastructure:**
    ```bash
    docker-compose up -d
    ```

3.  **Install Dependencies & Build:**
    ```bash
    npm install
    npm run build
    ```

4.  **Run Database Migrations (First time only):**
    ```bash
    npm --workspace apps/api run typeorm migration:run
    ```

5.  **Start Backend & Frontend:**
    ```bash
    npm run dev:api
    npm run dev:web
    ```

6.  **Configure a Camera:** Use the Sentira UI to add a camera with a valid RTSP URL and credentials. Enable AI processing.

---

## 9. Recommended Phase 5 Roadmap

- **Advanced Object Tracking:** Integrate ByteTrack or a similar algorithm for robust object tracking to enhance temporal rule accuracy.
- **Low-Latency Streaming:** Implement a direct WebRTC pipeline for the Live Monitor to reduce glass-to-glass latency.
- **Performance & Scalability Testing:** Conduct load testing with a high number of concurrent camera streams to identify and resolve bottlenecks.
- **Advanced Rule Actions:** Expand the rule engine to support more complex actions, such as triggering external webhooks or integrating with other third-party systems.