import { CamerasService } from './cameras.service';

describe('CamerasService', () => {
  it('encrypts credentials and removes them from the returned camera', async () => {
    const repository: any = {
      create: jest.fn((value) => value),
      save: jest.fn(async (value) => ({ id: 'camera-1', ...value })),
      findOne: jest.fn(async () => null),
    };
    const encryption = { encrypt: jest.fn(() => 'encrypted-secret') };
    const entitlement = { withCameraSlot: jest.fn(async (_org, operation) => operation({ getRepository: () => repository })) };
    const service = new CamerasService(repository, encryption as any, entitlement as any, { findOneBy: jest.fn(async () => ({ id: 'site-1' })) } as any);

    const camera = await service.create('org-1', { name: 'Front', siteId: 'site-1', streamUrl: 'rtsp://camera', protocol: 'rtsp', password: 'secret' } as any);

    expect(encryption.encrypt).toHaveBeenCalledWith('secret');
    expect(camera).not.toHaveProperty('password');
    expect(camera).not.toHaveProperty('passwordEncrypted');
    expect(repository.save).toHaveBeenCalledWith(expect.objectContaining({ passwordEncrypted: 'encrypted-secret' }));
  });

  it('lists cameras only for the requested organization and excludes encrypted credentials', async () => {
    const repository: any = { find: jest.fn(async () => [{ id: 'camera-1', organizationId: 'org-1' }]) };
    const service = new CamerasService(repository, {} as any, {} as any, {} as any);
    await expect(service.findByOrganization('org-1')).resolves.toEqual([{ id: 'camera-1', organizationId: 'org-1' }]);
    expect(repository.find).toHaveBeenCalledWith({ where: { organizationId: 'org-1' } });
  });

  it('rejects private stream targets to prevent cloud-side SSRF', async () => {
    const service = new CamerasService({} as any, {} as any, {} as any, {} as any);

    await expect(service.create('org-1', { name: 'Local', siteId: 'site-1', streamUrl: 'rtsp://192.168.1.20/live', protocol: 'rtsp' } as any)).rejects.toThrow('Sentira Connector');
  });

  it('does not expose stream URLs or usernames in public camera responses', async () => {
    const repository: any = { find: jest.fn(async () => [{ id: 'camera-1', organizationId: 'org-1', streamUrl: 'rtsp://camera/live', username: 'operator' }]) };
    const service = new CamerasService(repository, {} as any, {} as any, {} as any);
    const [camera] = await service.findByOrganization('org-1');
    expect(camera).not.toHaveProperty('streamUrl');
    expect(camera).not.toHaveProperty('username');
  });
});
