import { MediaRetentionService } from './media-retention.service';

describe('MediaRetentionService', () => {
  it('deletes only expired tenant-scoped media and clears stale event references', async () => {
    const expired = {
      id: 'media-expired',
      organizationId: 'org-1',
      eventId: 'event-1',
      storageKey: 'organizations/org-1/cameras/cam-1/events/event-1/snapshot.jpg',
      expiresAt: new Date(Date.now() - 60_000),
    };
    const unexpired = {
      id: 'media-fresh',
      organizationId: 'org-1',
      eventId: 'event-2',
      storageKey: 'organizations/org-1/cameras/cam-1/events/event-2/snapshot.jpg',
      expiresAt: new Date(Date.now() + 60_000),
    };

    const mediaRepository: any = {
      find: jest.fn().mockResolvedValue([expired, unexpired]),
      delete: jest.fn().mockResolvedValue(undefined),
    };
    const events: any = {
      findOneBy: jest.fn().mockResolvedValue({ id: 'event-1', snapshotUrl: '/api/events/event-1/media/media-expired/signed?ttl=300', videoClipUrl: null }),
      save: jest.fn().mockResolvedValue(undefined),
    };
    const auditLogs: any = { save: jest.fn().mockResolvedValue(undefined) };
    const storage: any = {
      assertTenantScopedKey: jest.fn().mockReturnValue(true),
      deleteForOrganization: jest.fn().mockResolvedValue(undefined),
    };

    const service = new MediaRetentionService({} as any, mediaRepository, events, auditLogs, storage);

    const result = await service.cleanupExpiredMedia('org-1');

    expect(result.deletedCount).toBe(1);
    expect(result.failedCount).toBe(0);
    expect(result.skippedCount).toBe(1);
    expect(storage.deleteForOrganization).toHaveBeenCalledWith('org-1', expired.storageKey);
    expect(mediaRepository.delete).toHaveBeenCalledWith('media-expired');
    expect(events.save).toHaveBeenCalledWith(expect.objectContaining({ snapshotUrl: null }));
    expect(auditLogs.save).toHaveBeenCalledWith(expect.objectContaining({ action: 'media.retention.deleted', resourceId: 'media-expired' }));
  });

  it('does not delete expired media when MinIO removal fails', async () => {
    const expired = {
      id: 'media-bad',
      organizationId: 'org-1',
      eventId: 'event-3',
      storageKey: 'organizations/org-1/cameras/cam-1/events/event-3/snapshot.jpg',
      expiresAt: new Date(Date.now() - 60_000),
    };

    const mediaRepository: any = {
      find: jest.fn().mockResolvedValue([expired]),
      delete: jest.fn().mockResolvedValue(undefined),
    };
    const events: any = { findOneBy: jest.fn(), save: jest.fn() };
    const auditLogs: any = { save: jest.fn() };
    const storage: any = {
      assertTenantScopedKey: jest.fn().mockReturnValue(true),
      deleteForOrganization: jest.fn().mockRejectedValue(new Error('MinIO outage')),
    };

    const service = new MediaRetentionService({} as any, mediaRepository, events, auditLogs, storage);

    const result = await service.cleanupExpiredMedia('org-1');

    expect(result.deletedCount).toBe(0);
    expect(result.failedCount).toBe(1);
    expect(mediaRepository.delete).not.toHaveBeenCalled();
    expect(auditLogs.save).not.toHaveBeenCalled();
  });
});
