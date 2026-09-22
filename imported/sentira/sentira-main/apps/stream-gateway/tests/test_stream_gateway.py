import importlib.util
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import HTTPException
import jwt

spec = importlib.util.spec_from_file_location('stream_gateway_main', Path(__file__).parents[1] / 'main.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
playback = module.playback
verify_internal_token = module.verify_internal_token
scoped_authorization = module.scoped_authorization

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


def make_scoped_token(**overrides):
    claims = {
        'iss': 'sentira-api',
        'aud': 'sentira-stream-gateway',
        'sub': 'user-a',
        'jti': 'request-a',
        'organizationId': 'org-a',
        'siteId': 'site-a',
        'cameraId': 'camera-a',
        'operation': 'playback',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(seconds=60),
    }
    claims.update(overrides)
    return jwt.encode(claims, 'stream-authorization-secret-that-is-long-enough', algorithm='HS256')


def test_gateway_rejects_missing_expired_and_mismatched_scoped_authorization(monkeypatch):
    monkeypatch.setattr(module.settings, 'STREAM_GATEWAY_AUTH_SECRET', 'stream-authorization-secret-that-is-long-enough')
    module.stream_manager.camera_configs['camera-a'] = {'organizationId': 'org-a', 'siteId': 'site-a'}
    dependency = scoped_authorization('playback')

    for authorization in (None, 'Bearer invalid'):
        try:
            asyncio.run(dependency('camera-a', authorization))
        except HTTPException as error:
            assert error.status_code == 401
        else:
            raise AssertionError('invalid scoped authorization was accepted')

    try:
        asyncio.run(dependency('camera-a', f'Bearer {make_scoped_token(operation="stop")}'))
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError('wrong operation scope was accepted')

    expired = make_scoped_token(exp=datetime.now(timezone.utc) - timedelta(seconds=1))
    try:
        asyncio.run(dependency('camera-a', f'Bearer {expired}'))
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError('expired scoped authorization was accepted')


def test_gateway_accepts_only_matching_camera_and_tenant_scope(monkeypatch):
    monkeypatch.setattr(module.settings, 'STREAM_GATEWAY_AUTH_SECRET', 'stream-authorization-secret-that-is-long-enough')
    module.stream_manager.camera_configs['camera-a'] = {'organizationId': 'org-a', 'siteId': 'site-a'}
    dependency = scoped_authorization('playback')

    claims = asyncio.run(dependency('camera-a', f'Bearer {make_scoped_token()}'))
    assert claims['organizationId'] == 'org-a'

    try:
        asyncio.run(dependency('camera-a', f'Bearer {make_scoped_token(organizationId="org-b")}'))
    except HTTPException as error:
        assert error.status_code == 404
    else:
        raise AssertionError('cross-tenant camera scope was accepted')

    try:
        asyncio.run(dependency('camera-a', f'Bearer {make_scoped_token(siteId="site-b")}'))
    except HTTPException as error:
        assert error.status_code == 404
    else:
        raise AssertionError('cross-site camera scope was accepted')

    try:
        asyncio.run(dependency('camera-b', f'Bearer {make_scoped_token()}'))
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError('wrong-camera scope was accepted')
