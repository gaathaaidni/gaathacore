import asyncio
from pathlib import Path
from fixture_publisher import command
from media_paths import media_path
from rolling_buffer import RollingBuffer

def test_fixture_publisher_uses_synthetic_video():
    args = command(media_path('org-a', 'site-a', 'camera-a'), 'mediamtx')
    assert 'testsrc2=size=640x360:rate=10' in args
    assert args[-1] == 'rtsp://mediamtx:8554/sentira/org-a/site-a/camera-a'


def test_media_path_is_bound_to_all_trusted_ids():
    assert media_path('org-a', 'site-a', 'camera-a') != media_path('org-b', 'site-a', 'camera-a')
    assert media_path('org-a', 'site-a', 'camera-a') != media_path('org-a', 'site-b', 'camera-a')


def test_media_path_rejects_untrusted_path_fragments():
    try:
        media_path('org-a/other-org', 'site-a', 'camera-a')
    except ValueError:
        pass
    else:
        raise AssertionError('unsafe media path fragment was accepted')

def test_missing_segments_do_not_claim_clip(tmp_path: Path):
    buffer = RollingBuffer(str(tmp_path), 'camera-a', 2, 120)
    assert asyncio.run(buffer.assemble_clip(0, 1, tmp_path / 'clip.mp4')) is None
