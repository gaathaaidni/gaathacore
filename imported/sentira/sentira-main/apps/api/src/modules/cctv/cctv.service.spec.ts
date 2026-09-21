import { NotFoundException } from '@nestjs/common';
import { CctvService } from './cctv.service';

function makeService() {
  const manufacturers: any = {};
  const models: any = { findOne: jest.fn() };
  const guides: any = {};
  const sessions: any = {
    create: jest.fn((value) => value),
    save: jest.fn(async (value) => ({ id: 'setup-1', ...value })),
    findOne: jest.fn(),
  };
  const support: any = {
    create: jest.fn((value) => value),
    save: jest.fn(async (value) => ({ id: 'support-1', createdAt: new Date(), status: 'OPEN', priority: 'NORMAL', ...value })),
  };
  const tests: any = {
    create: jest.fn((value) => value),
    save: jest.fn(async (value) => value),
    find: jest.fn(),
  };
  const cameras: any = { findOne: jest.fn() };
  const connectors: any = { create: jest.fn((value) => value), save: jest.fn(async (value) => ({ id: 'connector-1', ...value })), findOne: jest.fn() };
  const recorders: any = { findOne: jest.fn() };
  const channels: any = { find: jest.fn() };
  const discovered: any = { create: jest.fn((value) => value), save: jest.fn(async (value) => value) };
  const sites: any = { findOne: jest.fn() };
  const audit: any = { create: jest.fn((value) => value), save: jest.fn() };
  const commands: any = {
    create: jest.fn((value) => value),
    save: jest.fn(async (value) => ({ id: 'command-1', ...value })),
    findOne: jest.fn(),
    find: jest.fn(),
    createQueryBuilder: jest.fn(() => ({ where: jest.fn().mockReturnThis(), andWhere: jest.fn().mockReturnThis(), orderBy: jest.fn().mockReturnThis(), limit: jest.fn().mockReturnThis(), getMany: jest.fn().mockResolvedValue([]) })),
  };
  const rtsp: any = { testStream: jest.fn() };
  const onvif: any = { testStream: jest.fn() };
  const service = new CctvService(manufacturers, models, guides, sessions, support, tests, connectors, recorders, channels, discovered, cameras, sites, audit, commands, rtsp, onvif);
  return { service, sessions, support, tests, connectors, recorders, channels, discovered, cameras, sites, audit, commands, rtsp, onvif };
}

const user = { id: 'user-a', organizationId: 'org-a' } as any;

describe('CctvService', () => {
  it('creates an organization-scoped resumable setup session', async () => {
    const { service, sessions, sites } = makeService();
    sites.findOne.mockResolvedValue({ id: 'site-a', organizationId: 'org-a' });

    const result = await service.createSession(user, { deviceType: 'NVR', siteId: 'site-a' });

    expect(result).toEqual(expect.objectContaining({ id: 'setup-1', organizationId: 'org-a', deviceType: 'NVR', status: 'STARTED', completionPercent: 0 }));
    expect(sessions.create).toHaveBeenCalledWith(expect.objectContaining({ organizationId: 'org-a', userId: 'user-a', siteId: 'site-a' }));
  });

  it('prevents access to another organization setup session', async () => {
    const { service, sessions } = makeService();
    sessions.findOne.mockResolvedValue(null);

    await expect(service.getSession(user, 'setup-b')).rejects.toBeInstanceOf(NotFoundException);
    expect(sessions.findOne).toHaveBeenCalledWith({ where: { id: 'setup-b', organizationId: 'org-a' } });
  });

  it('finds an active setup session for resume', async () => {
    const { service, sessions } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'setup-1', status: 'IN_PROGRESS' });

    await expect(service.getActiveSession(user)).resolves.toEqual({ id: 'setup-1', status: 'IN_PROGRESS' });
    expect(sessions.findOne).toHaveBeenCalledWith(expect.objectContaining({ where: expect.any(Array) }));
  });

  it('returns structured non-technical connection results', async () => {
    const { service, sessions, cameras } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'setup-1', organizationId: 'org-a', status: 'IN_PROGRESS', stage: 'CONNECT' });
    cameras.findOne.mockResolvedValue({ id: 'camera-1', organizationId: 'org-a', sourceType: 'manual', status: 'offline' });

    await expect(service.testSession(user, 'setup-1', { cameraId: 'camera-1' })).resolves.toEqual(expect.objectContaining({ status: 'NETWORK_UNREACHABLE', retryable: true }));
  });

  it('rejects completion without a verified connection', async () => {
    const { service, sessions } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'setup-1', organizationId: 'org-a', status: 'IN_PROGRESS', testResult: { status: 'SETUP_INCOMPLETE' } });

    await expect(service.completeSession(user, 'setup-1', 'camera-1')).rejects.toThrow('verified camera connection');
    expect(sessions.save).not.toHaveBeenCalled();
  });

  it('rejects completion when the verified camera is not owned by the organization', async () => {
    const { service, sessions, cameras } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'setup-1', organizationId: 'org-a', status: 'VERIFIED', testResult: { status: 'VERIFIED_CONNECTED' } });
    cameras.findOne.mockResolvedValue(null);

    await expect(service.completeSession(user, 'setup-1', 'camera-b')).rejects.toThrow('Verified camera not found');
  });

  it('does not allow the client to force workflow state', async () => {
    const { service, sessions } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'setup-1', organizationId: 'org-a', status: 'IN_PROGRESS', stage: 'CONNECT', completionPercent: 65 });

    await service.updateSession(user, 'setup-1', { currentStep: 'test', answers: { deviceType: 'NVR' } });
    expect(sessions.save).toHaveBeenCalledWith(expect.objectContaining({ status: 'IN_PROGRESS', stage: 'TEST', completionPercent: 80 }));
  });

  it('removes credential-like fields from support context', async () => {
    const { service, support, cameras, sites } = makeService();
    sites.findOne.mockResolvedValue({ id: 'site-a', organizationId: 'org-a' });
    cameras.findOne.mockResolvedValue({ id: 'camera-a', organizationId: 'org-a' });

    await service.createSupportRequest(user, { siteId: 'site-a', cameraId: 'camera-a', reason: 'SETUP_HELP', message: 'password=secret', context: { password: 'secret', nested: { accessToken: 'token', step: 3 }, items: [{ credential: 'secret', label: 'safe' }] } });

    expect(support.create).toHaveBeenCalledWith(expect.objectContaining({ message: 'password=[redacted]', context: { nested: { step: 3 }, items: [{ label: 'safe' }] } }));
  });

  it('creates a short-lived pairing code and registers a connector once', async () => {
    const { service, sessions, connectors } = makeService();
    sessions.findOne.mockResolvedValue({ id: 'setup-1', organizationId: 'org-a', status: 'IN_PROGRESS' });
    const pairing = await service.createConnectorPairing(user, 'setup-1');
    expect(pairing.pairingCode).toMatch(/^[A-F0-9]{4}-[A-F0-9]{4}$/);
    expect(sessions.save).toHaveBeenCalledWith(expect.objectContaining({ pairingCodeHash: expect.any(String), pairingExpiresAt: expect.any(Date) }));

    sessions.findOne.mockResolvedValue({ id: 'setup-1', organizationId: 'org-a', pairingCodeHash: service['hash'](pairing.pairingCode), pairingExpiresAt: new Date(Date.now() + 60_000), pairingUsedAt: null });
    const result = await service.registerConnector('setup-1', { pairingCode: pairing.pairingCode, connectorName: 'Office Edge' });
    expect(result).toEqual(expect.objectContaining({ connectorId: 'connector-1', registrationToken: expect.any(String) }));
    expect(connectors.save).toHaveBeenCalledWith(expect.objectContaining({ registrationTokenHash: expect.any(String), organizationId: 'org-a' }));
  });

  it('authenticates connector heartbeat and does not fake local discovery', async () => {
    const { service, connectors, sessions } = makeService();
    const token = 'connector-token';
    connectors.findOne.mockResolvedValue({ id: 'connector-1', organizationId: 'org-a', registrationTokenHash: service['hash'](token), status: 'offline' });
    await expect(service.heartbeatConnector({ connectorId: 'connector-1', registrationToken: token })).resolves.toEqual(expect.objectContaining({ connectorId: 'connector-1', status: 'online' }));
    sessions.findOne.mockResolvedValue({ id: 'setup-1', connectorId: 'connector-1', organizationId: 'org-a' });
    await expect(service.discoverThroughConnector({ setupSessionId: 'setup-1', connectorId: 'connector-1', registrationToken: token })).resolves.toEqual(expect.objectContaining({ status: 'DISCOVERY_UNAVAILABLE', cameras: [] }));
  });

  it('creates a queued connector command and rejects cross-tenant access', async () => {
    const { service, connectors, commands } = makeService();
    connectors.findOne.mockResolvedValue({ id: 'connector-1', organizationId: 'org-a', registrationTokenHash: service['hash']('token-a'), status: 'online' });
    commands.save.mockResolvedValue({ id: 'command-1', organizationId: 'org-a', connectorId: 'connector-1', status: 'QUEUED', commandType: 'PING' });

    await expect(service.createConnectorCommand(user, { connectorId: 'connector-1', commandType: 'PING', payload: { ok: true }, maxAttempts: 2, expiresInSeconds: 30 })).resolves.toEqual(expect.objectContaining({ status: 'QUEUED', commandType: 'PING' }));
    await expect(service.getConnectorCommandsForPolling('connector-1', 'token-a', 5, 10)).resolves.toEqual(expect.any(Array));
    await expect(service.getConnectorCommandsForPolling('connector-1', 'wrong-token', 5, 10)).rejects.toThrow();
    const another = { id: 'user-b', organizationId: 'org-b' } as any;
    connectors.findOne.mockResolvedValue({ id: 'connector-2', organizationId: 'org-b', registrationTokenHash: service['hash']('token-b'), status: 'online' });
    await expect(service.createConnectorCommand(another, { connectorId: 'connector-1', commandType: 'PING', payload: { ok: true }, maxAttempts: 2, expiresInSeconds: 30 })).rejects.toThrow();
  });

  it('accepts valid results and rejects stale or wrong-connector results', async () => {
    const { service, connectors, commands } = makeService();
    connectors.findOne.mockResolvedValue({ id: 'connector-1', organizationId: 'org-a', registrationTokenHash: service['hash']('token-a'), status: 'online' });
    commands.findOne.mockResolvedValue({ id: 'command-1', connectorId: 'connector-1', organizationId: 'org-a', status: 'ACKNOWLEDGED', expiresAt: new Date(Date.now() + 60_000), commandType: 'PING' });

    await expect(service.reportConnectorCommandResult('connector-1', 'token-a', 'command-1', { status: 'SUCCEEDED', result: { ok: true } })).resolves.toEqual(expect.objectContaining({ status: 'SUCCEEDED' }));
    commands.findOne.mockResolvedValue({ id: 'command-1', connectorId: 'connector-2', organizationId: 'org-a', status: 'ACKNOWLEDGED', expiresAt: new Date(Date.now() + 60_000), commandType: 'PING' });
    await expect(service.reportConnectorCommandResult('connector-1', 'token-a', 'command-1', { status: 'SUCCEEDED', result: { ok: true } })).rejects.toThrow('does not belong');
  });
});
