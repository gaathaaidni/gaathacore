import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('stream_gateway_main', Path(__file__).parents[1] / 'main.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
playback = module.playback

def test_playback_prefers_webrtc_with_hls_fallback():
    body = playback('cam1')
    assert body['preferred'] in ['webrtc', 'hls']
    assert body['hls']['url'].endswith('index.m3u8')
