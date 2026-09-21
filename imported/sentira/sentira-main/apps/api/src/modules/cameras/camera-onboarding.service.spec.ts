import { BadRequestException, NotFoundException } from '@nestjs/common';
import { CameraOnboardingService } from './camera-onboarding.service';

describe('CameraOnboardingService', () => {
  const makeService = () => {
    const sessions: any = { create: jest.fn((value) => value), save: jest.fn(async (value) => ({ id: 'session-1', ...value })), findOne: jest.fn() };
    const connectors: any = { create: jest.fn((value) => value), save: jest.fn(async (value) => ({ id: 'connector-1', ...value })), findOne: jest.fn() };
    const discovered: any = { find: jest.fn(), findOne: jest.fn(), create: jest.fn((value) => value), save: jest.fn(async (value) => ({ id: 'discovered-1', ...value })) };
    const cameras: any = {};
    const sites: any = { findOne: jest.fn() };
    const audit: any = { create: jest.fn((value) => value), save: jest.fn() };
    const entitlement: any = {};
    return { service: new CameraOnboardingService(sessions, connectors, discovered, cameras, sites, audit, entitlement), sessions, connectors, discovered, sites };
  };

  it('creates a short-lived session and only returns the pairing code once', async () => {
    const { service, sessions } = makeService();
    const result = await service.createSession('org-a', 'user-a', { method: 'automatic' });
    expect(result).toEqual(expect.objectContaining({ id: 'session-1', pairingCode: expect.stringMatching(/^[A-F0-9]{4}-[A-F0-9]{4}$/), connectorRequired: true }));
    expect(sessions.create).toHaveBeenCalledWith(expect.objectContaining({ organizationId: 'org-a', userId: 'user-a', method: 'automatic', pairingCodeHash: expect.any(String), expiresAt: expect.any(Date) }));
  });

  it('does not list another organization\'s onboarding session', async () => {
    const { service, sessions } = makeService();
    sessions.findOne.mockResolvedValue(null);
    await expect(service.listDiscovered('org-a', 'session-b')).rejects.toBeInstanceOf(NotFoundException);
    expect(sessions.findOne).toHaveBeenCalledWith({ where: { id: 'session-b', organizationId: 'org-a' } });
  });

  it('rejects expired or already-used pairing codes', async () => {
    const { service, sessions } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'session-1', organizationId: 'org-a', expiresAt: new Date(Date.now() - 1000), usedAt: null });
    await expect(service.pairConnector('org-a', 'session-1', { pairingCode: 'ABCD-1234', connectorName: 'Office connector' }, 'user-a')).rejects.toBeInstanceOf(BadRequestException);
  });

  it('rejects claiming a discovered camera from another organization', async () => {
    const { service, discovered } = makeService();
    discovered.findOne.mockResolvedValue(null);
    await expect(service.claim('org-a', 'user-a', { discoveredCameraId: 'camera-b', siteId: 'site-a', name: 'Front Door' })).rejects.toBeInstanceOf(NotFoundException);
    expect(discovered.findOne).toHaveBeenCalledWith({ where: { id: 'camera-b', organizationId: 'org-a', discoveryStatus: 'ready' } });
  });
});
