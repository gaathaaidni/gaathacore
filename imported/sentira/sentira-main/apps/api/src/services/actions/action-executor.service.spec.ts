import { ActionExecutorService } from './action-executor.service';

describe('ActionExecutorService', () => {
  it('queues non-webhook actions without blocking event creation', async () => {
    await expect(new ActionExecutorService().execute({ type: 'notify' }, { eventId: 'e1', organizationId: 'o1', cameraId: 'c1', eventType: 'test', severity: 'low', timestamp: new Date().toISOString() })).resolves.toEqual(expect.objectContaining({ status: 'queued' }));
  });
});
