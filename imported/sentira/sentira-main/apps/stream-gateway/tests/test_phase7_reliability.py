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


def test_camera_reconciliation_stops_disabled_and_deleted_streams(monkeypatch):
    manager = CameraStreamManager()
    manager.camera_configs['camera-a'] = {
        'id': 'camera-a', 'organizationId': 'org-a', 'siteId': 'site-a',
        'streamUrl': 'rtsp://source-a/live', 'isEnabled': True,
    }

    async def fake_fetch_disabled():
        return [{
            'id': 'camera-a', 'organizationId': 'org-a', 'siteId': 'site-a',
            'streamUrl': 'rtsp://source-a/live', 'isEnabled': False,
        }]

    async def fake_fetch_deleted():
        return []

    async def exercise():
        await manager.start_stream_by_id('camera-a')
        await manager.load_and_start_cameras()
        assert manager.statuses['camera-a'].state == 'DISABLED'
        assert 'camera-a' not in manager.streams
        manager.camera_configs['camera-a']['isEnabled'] = True
        await manager.start_stream_by_id('camera-a')
        monkeypatch.setattr(manager, '_fetch_all_cameras', fake_fetch_deleted)
        await manager.load_and_start_cameras()
        assert 'camera-a' not in manager.camera_configs
        assert 'camera-a' not in manager.streams

    monkeypatch.setattr(manager, '_fetch_all_cameras', fake_fetch_disabled)
    asyncio.run(exercise())


def test_two_tenant_publication_paths_are_distinct_and_credential_free(monkeypatch):
    monkeypatch.setattr(settings, 'MEDIAMTX_RTSP_URL', 'rtsp://mediamtx:8554')
    monkeypatch.setattr(settings, 'SENTIRA_MEDIA_PUBLISH_TOKEN', 'local-publish-token')
    manager = CameraStreamManager()
    camera_a = {
        'id': 'camera-a', 'organizationId': 'org-a', 'siteId': 'site-a',
        'streamUrl': 'rtsp://source-a/live',
    }
    camera_b = {
        'id': 'camera-b', 'organizationId': 'org-b', 'siteId': 'site-b',
        'streamUrl': 'rtsp://source-b/live',
    }
    command_a = manager._media_publication_command(camera_a)
    command_b = manager._media_publication_command(camera_b)
    assert command_a[-1].endswith('/sentira/org-a/site-a/camera-a?token=local-publish-token')
    assert command_b[-1].endswith('/sentira/org-b/site-b/camera-b?token=local-publish-token')
    assert command_a[-1] != command_b[-1]
    assert 'camera-password' not in ' '.join(command_a + command_b)


class _FakeProcess:
    def __init__(self):
        self.returncode = None
        self.terminated = False
        self.killed = False

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.killed = True
        self.returncode = -9

    async def wait(self):
        return self.returncode


def test_manager_cleanup_terminates_all_three_children():
    async def run():
        manager = CameraStreamManager()
        processes = [_FakeProcess(), _FakeProcess(), _FakeProcess()]
        manager.processes['camera-a'] = processes
        await manager._terminate_processes('camera-a')
        assert all(process.terminated for process in processes)
        assert 'camera-a' not in manager.processes

    asyncio.run(run())
