# Phase 5 Tracking

Status: PARTIALLY IMPLEMENTED and TESTED for the lightweight Python provider.

Sentira now defines a `TrackingProvider` contract with `track()`, `reset()`, and `getTracks()`. The first implementation is `LightweightTrackingProvider`, an IoU-based tracker with bounded state, configurable `TRACK_MAX_AGE`, `TRACK_IOU_THRESHOLD`, and `TRACK_MIN_HITS`, stable track IDs across nearby frames, temporary lost-track handling, and automatic stale cleanup.

ByteTrack remains a future provider option; it was not integrated because the repository did not include an AI worker implementation or pinned CV runtime suitable for a safe production dependency swap.
