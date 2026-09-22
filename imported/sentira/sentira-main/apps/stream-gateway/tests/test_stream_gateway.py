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
authorize_media = module.authorize_media
MediaAuthRequest = module.MediaAuthRequest

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


def test_media_auth_rejects_cross_tenant_expired_and_disabled_requests(monkeypatch):
    monkeypatch.setattr(module.settings, 'STREAM_GATEWAY_AUTH_SECRET', 'stream-authorization-secret-that-is-long-enough')
    monkeypatch.setattr(module, '_current_camera', lambda camera_id: asyncio.sleep(0, result={
        'id': camera_id,
        'organizationId': 'org-a',
        'siteId': 'site-a',
        'isEnabled': camera_id == 'camera-a',
    }))

    valid = make_scoped_token()
    assert asyncio.run(authorize_media(MediaAuthRequest(token=valid, action='read', protocol='hls', path='sentira/org-a/site-a/camera-a'))) is None

    for token, path in (
        (make_scoped_token(organizationId='org-b'), 'sentira/org-b/site-b/camera-b'),
        (make_scoped_token(exp=datetime.now(timezone.utc) - timedelta(seconds=1)), 'sentira/org-a/site-a/camera-a'),
        (valid, 'sentira/org-a/site-a/camera-b'),
    ):
        try:
            asyncio.run(authorize_media(MediaAuthRequest(token=token, action='read', protocol='hls', path=path)))
        except HTTPException as error:
            assert error.status_code in (401, 403)
        else:
            raise AssertionError('unauthorized media request was accepted')

    disabled_token = make_scoped_token(cameraId='camera-b', organizationId='org-a', siteId='site-a')
    try:
        asyncio.run(authorize_media(MediaAuthRequest(token=disabled_token, action='read', protocol='hls', path='sentira/org-a/site-a/camera-b')))
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError('disabled camera media request was accepted')


def test_media_auth_accepts_only_configured_publication_token(monkeypatch):
    monkeypatch.setattr(module.settings, 'SENTIRA_MEDIA_PUBLISH_TOKEN', 'local-publish-token')
    request = MediaAuthRequest(token='local-publish-token', action='publish', protocol='rtsp', path='sentira/org-a/site-a/camera-a')
    assert asyncio.run(authorize_media(request)) is None

    try:
        asyncio.run(authorize_media(request.model_copy(update={'token': 'wrong-token'})))
    except HTTPException as error:
        assert error.status_code == 403
    else:
        raise AssertionError('invalid publication token was accepted')
