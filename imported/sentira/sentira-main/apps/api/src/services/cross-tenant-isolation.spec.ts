import { NotFoundException } from '@nestjs/common';
import { CamerasService } from '../modules/cameras/cameras.service';
import { EventsService } from '../modules/events/events.service';
import { EvidenceService } from './evidence.service';

describe('tenant isolation regressions', () => {
  it('camera lookups are scoped to the caller organization', async () => {
    const cameraRepository: any = { findOne: jest.fn().mockResolvedValue(null) };
    const service = new CamerasService(
      cameraRepository,
      { encrypt: jest.fn(), decrypt: jest.fn() } as any,
      {} as any,
      { findOneBy: jest.fn() } as any,
    );

    await expect(service.findById('camera-1', 'org-b')).resolves.toBeNull();
    expect(cameraRepository.findOne).toHaveBeenCalledWith({
      where: { id: 'camera-1', organizationId: 'org-b' },
    });
  });

  it('event lookups are scoped to the caller organization', async () => {
    const eventRepository: any = { findOne: jest.fn().mockResolvedValue(null) };
    const service = new EventsService(eventRepository, { save: jest.fn() } as any);

    await expect(service.findById('event-1', 'org-b')).resolves.toBeNull();
    expect(eventRepository.findOne).toHaveBeenCalledWith({
      where: { id: 'event-1', organizationId: 'org-b' },
      relations: ['camera', 'site', 'rule', 'zone'],
    });
  });

  it('evidence lookups reject cross-tenant media access', async () => {
    const mediaRepository: any = { findOneBy: jest.fn().mockResolvedValue(null) };
    const service = new EvidenceService(mediaRepository, {} as any, {} as any, { get: jest.fn() } as any);

    await expect(service.findAuthorized('media-1', 'event-1', 'org-b')).rejects.toBeInstanceOf(NotFoundException);
    expect(mediaRepository.findOneBy).toHaveBeenCalledWith({
      id: 'media-1',
      eventId: 'event-1',
      organizationId: 'org-b',
    });
  });

  it('authorized evidence reads are restricted to the tenant storage namespace', async () => {
    const media = { id: 'media-1', eventId: 'event-1', organizationId: 'org-b', storageKey: 'organizations/org-b/cameras/cam-1/events/event-1/snapshot.jpg', contentType: 'image/jpeg' };
    const mediaRepository: any = { findOneBy: jest.fn().mockResolvedValue(media) };
    const storage: any = { getForOrganization: jest.fn().mockResolvedValue(Buffer.from('abc')) };
    const service = new EvidenceService(mediaRepository, {} as any, {} as any, storage);

    await expect(service.readAuthorized('media-1', 'event-1', 'org-b')).resolves.toEqual(expect.objectContaining({ media }));
    expect(storage.getForOrganization).toHaveBeenCalledWith('org-b', media.storageKey);
  });

  it('clamps signed media URLs to a short, bounded TTL', async () => {
    const service = new EvidenceService({} as any, {} as any, {} as any, { getForOrganization: jest.fn() } as any);

    expect(service.signedAccessPath({ eventId: 'event-1', id: 'media-1' } as any, 999999)).toBe('/api/events/event-1/media/media-1/signed?ttl=300');
    expect(service.signedAccessPath({ eventId: 'event-1', id: 'media-1' } as any, 0)).toBe('/api/events/event-1/media/media-1/signed?ttl=300');
  });
});
