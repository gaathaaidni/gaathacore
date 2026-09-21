from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol, Tuple
import os, uuid

BBox = Tuple[float, float, float, float]

@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: BBox
    camera_id: str
    organization_id: str
    site_id: Optional[str] = None
    zone_ids: List[str] = field(default_factory=list)

@dataclass
class Track:
    trackId: str
    cameraId: str
    organizationId: str
    siteId: Optional[str]
    className: str
    confidence: float
    bbox: BBox
    firstSeen: str
    lastSeen: str
    lastUpdated: str
    velocity: Optional[Dict[str, float]] = None
    zoneIds: List[str] = field(default_factory=list)
    state: str = "tentative"
    hits: int = 1
    age: int = 0

class TrackingProvider(Protocol):
    def track(self, detections: List[Detection], timestamp: Optional[datetime] = None) -> List[Track]: ...
    def reset(self) -> None: ...
    def getTracks(self) -> List[Track]: ...

def iou(a: BBox, b: BBox) -> float:
    ax1, ay1, aw, ah = a; bx1, by1, bw, bh = b
    ax2, ay2, bx2, by2 = ax1 + aw, ay1 + ah, bx1 + bw, by1 + bh
    ix1, iy1, ix2, iy2 = max(ax1, bx1), max(ay1, by1), min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0

class LightweightTrackingProvider:
    def __init__(self, max_age: Optional[int] = None, iou_threshold: Optional[float] = None, min_hits: Optional[int] = None):
        self.max_age = int(max_age if max_age is not None else os.getenv("TRACK_MAX_AGE", "8"))
        self.iou_threshold = float(iou_threshold if iou_threshold is not None else os.getenv("TRACK_IOU_THRESHOLD", "0.25"))
        self.min_hits = int(min_hits if min_hits is not None else os.getenv("TRACK_MIN_HITS", "2"))
        self._tracks: Dict[str, Track] = {}

    def track(self, detections: List[Detection], timestamp: Optional[datetime] = None) -> List[Track]:
        now = (timestamp or datetime.now(timezone.utc)).isoformat()
        unmatched = set(self._tracks.keys())
        for det in detections:
            best_id, best_iou = None, 0.0
            for tid in list(unmatched):
                tr = self._tracks[tid]
                if tr.cameraId == det.camera_id and tr.className == det.class_name:
                    score = iou(tr.bbox, det.bbox)
                    if score > best_iou:
                        best_id, best_iou = tid, score
            if best_id and best_iou >= self.iou_threshold:
                tr = self._tracks[best_id]
                old_cx, old_cy = tr.bbox[0] + tr.bbox[2] / 2, tr.bbox[1] + tr.bbox[3] / 2
                new_cx, new_cy = det.bbox[0] + det.bbox[2] / 2, det.bbox[1] + det.bbox[3] / 2
                tr.velocity = {"x": new_cx - old_cx, "y": new_cy - old_cy}
                tr.bbox, tr.confidence, tr.lastSeen, tr.lastUpdated = det.bbox, det.confidence, now, now
                tr.zoneIds, tr.hits, tr.age = det.zone_ids, tr.hits + 1, 0
                tr.state = "confirmed" if tr.hits >= self.min_hits else "tentative"
                unmatched.remove(best_id)
            else:
                tid = f"trk_{uuid.uuid4().hex[:12]}"
                self._tracks[tid] = Track(tid, det.camera_id, det.organization_id, det.site_id, det.class_name, det.confidence, det.bbox, now, now, now, None, det.zone_ids)
        for tid in list(unmatched):
            self._tracks[tid].age += 1
            self._tracks[tid].state = "lost"
            if self._tracks[tid].age > self.max_age:
                del self._tracks[tid]
        return self.getTracks()

    def reset(self) -> None:
        self._tracks.clear()

    def getTracks(self) -> List[Track]:
        return list(self._tracks.values())
