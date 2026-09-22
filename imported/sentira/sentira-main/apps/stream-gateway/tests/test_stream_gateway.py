import importlib.util
import asyncio
from pathlib import Path
from fastapi import HTTPException

spec = importlib.util.spec_from_file_location('stream_gateway_main', Path(__file__).parents[1] / 'main.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
playback = module.playback
verify_internal_token = module.verify_internal_token

def test_playback_prefers_webrtc_with_hls_fallback():
    body = playback('cam1')
    assert body['preferred'] in ['webrtc', 'hls']
    assert body['hls']['url'].endswith('index.m3u8')


def test_gateway_rejects_missing_or_invalid_internal_tokens(monkeypatch):
    monkeypatch.setattr(module.settings, 'STREAM_GATEWAY_INTERNAL_TOKEN', '')
    for token in (None, 'wrong-token'):
        try:
            asyncio.run(verify_internal_token(token))
        except HTTPException as error:
            assert error.status_code == 401
        else:
            raise AssertionError('invalid gateway token was accepted')


def test_gateway_accepts_configured_internal_token(monkeypatch):
    monkeypatch.setattr(module.settings, 'STREAM_GATEWAY_INTERNAL_TOKEN', 'gateway-secret')
    assert asyncio.run(verify_internal_token('gateway-secret')) is None
