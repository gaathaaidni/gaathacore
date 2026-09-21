# Sentira AI Pipeline

## High-level flow

Phase 10G verified real fixture frames reaching the AI Worker, RabbitMQ, API
consumer, and persisted event path.

```text
Camera Stream
  -> Stream Manager
  -> Frame Sampling
  -> Video Processor
  -> AI Provider
  -> Detection Provider
  -> Tracking Provider
  -> Rule Engine
  -> Event Classification
  -> Evidence Recording
  -> Notification Engine
  -> Dashboard Update
```

## Abstraction interfaces

```ts
interface AIProvider {
  processFrame(frame: Buffer): Promise<DetectionResult[]>;
}

interface DetectionProvider {
  detect(frame: Buffer): Promise<DetectionResult[]>;
}

interface TrackingProvider {
  updateTrack(detections: DetectionResult[]): Promise<TrackState[]>;
}

interface EventClassifier {
  classify(eventContext: EventContext): Promise<EventClassification>;
}
```

## Supported model types

- YOLO
- RT-DETR
- TensorRT-optimized models
- OpenCV pipelines
- custom CV models
- vision-language models where appropriate

## Important design principle

The rule engine must consume normalized detections, not model-specific outputs. This allows swapping models without rewriting the business logic.

## Configurable runtime controls

- FPS
- resolution
- inference interval
- confidence threshold
- model selection
- worker pool size
- queue policies

## Production notes

- Use asynchronous workers for inference
- Reduce computation by sampling frames at configured intervals
- Keep rolling buffers for evidence capture before and after events
- Use GPU acceleration when available, with CPU fallback for demo or low-load deployments

## Phase 6 backpressure

AI frame rate remains configurable at system and camera level. High-frequency detections are throttled through rule cooldown/duplicate windows, queue-first notification delivery, and evidence metadata queuing so expensive media operations do not block event creation.


## Phase 7 Production Operations
Sentira Phase 7 adds production AI provider abstraction, compact track IDs, behavioral rule primitives, camera health scoring, reconnect/backpressure strategy, evidence integrity metadata, event escalation/suppression, aggregation/reporting guidance, privacy/retention controls, observability correlation IDs, and disaster-recovery runbooks. Capabilities are industry-agnostic and organization-scoped; unverified external dependencies are explicitly documented in `PHASE_7_COMPLETION_REPORT.md`.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C detection contract

The deterministic provider remains integration-only. It validates base64 JPEG
markers and emits a normalized envelope containing model metadata, frame identity,
objects, timing, JPEG evidence payload, and correlation ID.

## Phase 10E verification status

The deterministic provider and normalized RabbitMQ envelope remain integration
fixtures only. AMQP dependency locking and live broker delivery were blocked by npm
HTTP 403 and unavailable Docker; no production inference or end-to-end delivery is
claimed. See `PHASE_10E_COMPLETION_REPORT.md`.
