import asyncio
from camera_manager import CameraStreamManager


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
