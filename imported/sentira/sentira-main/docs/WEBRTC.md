# WebRTC Architecture

Status: PARTIALLY IMPLEMENTED / NOT REAL-CAMERA VERIFIED.

The Stream Gateway now exposes a playback discovery endpoint returning WebRTC-first metadata with HLS fallback. The intended production provider is MediaMTX/WHEP, keeping RTSP credentials server-side and exposing only authenticated browser playback URLs. Real WebRTC media negotiation is not verified in this environment.
