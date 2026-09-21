import asyncio
from pathlib import Path
from fixture_publisher import command
from rolling_buffer import RollingBuffer

def test_fixture_publisher_uses_synthetic_video():
    args = command('fixture', 'mediamtx')
    assert 'testsrc2=size=640x360:rate=10' in args
    assert args[-1] == 'rtsp://mediamtx:8554/fixture'

def test_missing_segments_do_not_claim_clip(tmp_path: Path):
    buffer = RollingBuffer(str(tmp_path), 'camera-a', 2, 120)
    assert asyncio.run(buffer.assemble_clip(0, 1, tmp_path / 'clip.mp4')) is None
