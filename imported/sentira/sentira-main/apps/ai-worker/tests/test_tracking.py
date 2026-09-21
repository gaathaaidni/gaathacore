from datetime import datetime, timezone, timedelta
from tracking.provider import Detection, LightweightTrackingProvider

def test_track_id_persists_across_adjacent_frames():
    tracker = LightweightTrackingProvider(max_age=3, iou_threshold=0.2, min_hits=2)
    t = datetime.now(timezone.utc)
    first = tracker.track([Detection('person', .9, (0.1,0.1,0.2,0.2), 'cam1', 'org1')], t)[0]
    second = tracker.track([Detection('person', .88, (0.11,0.1,0.2,0.2), 'cam1', 'org1')], t + timedelta(seconds=1))[0]
    assert first.trackId == second.trackId
    assert second.state == 'confirmed'

def test_stale_tracks_are_bounded_and_cleaned():
    tracker = LightweightTrackingProvider(max_age=1, iou_threshold=0.2, min_hits=1)
    t = datetime.now(timezone.utc)
    tracker.track([Detection('person', .9, (0,0,1,1), 'cam1', 'org1')], t)
    tracker.track([], t + timedelta(seconds=1))
    tracker.track([], t + timedelta(seconds=2))
    assert tracker.getTracks() == []
