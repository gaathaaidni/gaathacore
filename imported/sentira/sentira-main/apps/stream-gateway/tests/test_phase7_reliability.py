import asyncio
from camera_manager import CameraStreamManager
from config import settings


def test_status_schema_and_disabled_state():
    manager = CameraStreamManager()
    manager.camera_configs['cam'] = {'id': 'cam', 'isEnabled': False, 'name': 'Disabled'}
    manager.statuses['cam'] = __import__('camera_manager').CameraRuntimeStatus(camera_id='cam', state='DISABLED')
    status = manager.get_all_statuses()['cam']
    assert status['state'] == 'DISABLED'
    assert 'health_score' in status


def test_one_task_per_camera_event_loop():
    async def run():
        manager = CameraStreamManager()
        manager.camera_configs['cam'] = {'id': 'cam', 'isEnabled': True, 'aiEnabled': True, 'name': 'Camera'}
        assert await manager.start_stream_by_id('cam') is True
        first = manager.streams['cam']
        assert await manager.start_stream_by_id('cam') is True
        assert manager.streams['cam'] is first
        assert await manager.stop_stream_by_id('cam') is True
    asyncio.run(run())


def test_media_publication_command_uses_trusted_camera_path(monkeypatch):
    monkeypatch.setattr(settings, 'MEDIAMTX_RTSP_URL', 'rtsp://mediamtx:8554')
    monkeypatch.setattr(settings, 'SENTIRA_MEDIA_PUBLISH_TOKEN', 'local-publish-token')
    manager = CameraStreamManager()
    command = manager._media_publication_command({
        'id': 'camera-a',
        'organizationId': 'org-a',
        'siteId': 'site-a',
        'streamUrl': 'rtsp://camera.example/live',
    })
    assert command[-1] == 'rtsp://mediamtx:8554/sentira/org-a/site-a/camera-a?token=local-publish-token'
    assert command[command.index('-i') + 1] == 'rtsp://camera.example/live'
    assert 'org-a' in command[-1]


def test_media_publication_command_rejects_untrusted_path_identifiers():
    manager = CameraStreamManager()
    try:
        manager._media_publication_command({
            'id': 'camera-a/other',
            'organizationId': 'org-a',
            'siteId': 'site-a',
            'streamUrl': 'rtsp://camera.example/live',
        })
    except ValueError:
        pass
    else:
        raise AssertionError('untrusted media path identifier was accepted')
