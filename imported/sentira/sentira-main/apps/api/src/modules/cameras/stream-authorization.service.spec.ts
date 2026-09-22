import { InternalServerErrorException, NotFoundException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { StreamAuthorizationService } from './stream-authorization.service';

const secret = 'stream-authorization-secret-that-is-long-enough';
const user = { id: 'user-1', organizationId: 'org-a', roleId: 'role-a' } as any;

describe('StreamAuthorizationService', () => {
  const makeService = (camera: any = { id: 'camera-a', organizationId: 'org-a', siteId: 'site-a' }, configuredSecret = secret) => {
    const cameras = { findOne: jest.fn().mockResolvedValue(camera) } as any;
    const sites = { findOne: jest.fn().mockResolvedValue({ id: 'site-a', organizationId: 'org-a' }) } as any;
    const config = { get: jest.fn().mockReturnValue(configuredSecret) } as any;
    return { service: new StreamAuthorizationService(cameras, sites, config), cameras, sites };
  };

  it('issues a short-lived token scoped to the requested camera operation', async () => {
    const { service } = makeService();

    const result = await service.issue(user, 'camera-a', 'start', 'request-1');
    const claims = new JwtService({ secret }).verify(result.authorizationToken, { audience: 'sentira-stream-gateway', issuer: 'sentira-api' });

    expect(result).toEqual(expect.objectContaining({ cameraId: 'camera-a', organizationId: 'org-a', siteId: 'site-a', operation: 'start', gatewayPath: '/streams/camera-a/start' }));
    expect(claims).toEqual(expect.objectContaining({ sub: 'user-1', organizationId: 'org-a', siteId: 'site-a', cameraId: 'camera-a', operation: 'start', requestId: 'request-1', jti: expect.any(String) }));
    expect(claims.exp - claims.iat).toBe(60);
  });

  it('rejects a camera from another organization before issuing a token', async () => {
    const { service, cameras, sites } = makeService(null);

    await expect(service.issue(user, 'camera-b', 'playback')).rejects.toBeInstanceOf(NotFoundException);
    expect(cameras.findOne).toHaveBeenCalledWith({ where: { id: 'camera-b', organizationId: 'org-a' } });
    expect(sites.findOne).not.toHaveBeenCalled();
  });

  it('fails closed when the gateway signing secret is missing', async () => {
    const { service } = makeService(undefined, '');

    await expect(service.issue(user, 'camera-a', 'status')).rejects.toBeInstanceOf(InternalServerErrorException);
  });
});