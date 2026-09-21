# Performance and Load Testing

Status: HARNESS CONCEPTUAL / BENCHMARKS NOT EXECUTED.

No benchmark numbers are reported because no real RTSP source or deployed stack was available. Phase 5 added bounded stream controls (`MAX_ACTIVE_STREAMS`) and AI tracking state limits. Recommended harness: run synthetic demo streams at 10, 25, 50, and 100 cameras and record CPU, RAM, GPU, FPS, queue depth, event latency, RabbitMQ backlog, Redis latency, and disk usage.
