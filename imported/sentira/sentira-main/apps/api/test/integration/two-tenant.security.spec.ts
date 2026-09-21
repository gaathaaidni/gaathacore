import request from 'supertest';
import { io } from 'socket.io-client';

const baseUrl = process.env.SENTIRA_API_URL || 'http://localhost:4000';
const enabled = process.env.SENTIRA_LIVE_INTEGRATION === '1';

type Account = {
  accessToken: string;
  refreshToken: string;
  user: { id: string; organizationId: string };
};

type Tenant = Account & { siteId: string; cameraIds: string[] };

const auth = (account: Account) => ({ Authorization: `Bearer ${account.accessToken}` });
const uniqueEmail = (label: string) => `phase11b-${label}-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;

async function signup(label: string): Promise<Account> {
  const response = await request(baseUrl).post('/api/auth/signup').send({
    email: uniqueEmail(label),
    password: 'Phase11B-safe-test-password-123!',
    organizationName: `Phase 11B ${label}`,
  });
  expect(response.status).toBe(201);
  expect(response.body).toEqual(expect.objectContaining({ accessToken: expect.any(String), refreshToken: expect.any(String) }));
  expect(response.body.user.organizationId).toEqual(expect.any(String));
  return response.body as Account;
}

async function createTenant(label: string): Promise<Tenant> {
  const account = await signup(label);
  const siteResponse = await request(baseUrl)
    .post(`/api/organizations/${account.user.organizationId}/sites`)
    .set(auth(account))
    .send({ name: `${label} site`, timezone: 'UTC' });
  expect(siteResponse.status).toBe(201);
  const siteId = siteResponse.body.id as string;
  const cameraIds: string[] = [];

  for (let index = 1; index <= 3; index += 1) {
    const cameraResponse = await request(baseUrl)
      .post('/api/cameras')
      .set(auth(account))
      .send({
        name: `${label} camera ${index}`,
        siteId,
        streamUrl: `rtsp://${label.toLowerCase()}.example.test/live/${index}`,
        protocol: 'rtsp',
        username: `${label.toLowerCase()}-camera`,
        password: 'safe-test-camera-password',
      });
    expect(cameraResponse.status).toBe(201);
    expect(cameraResponse.body).not.toHaveProperty('password');
    expect(cameraResponse.body).not.toHaveProperty('passwordEncrypted');
    cameraIds.push(cameraResponse.body.id);
  }
  return { ...account, siteId, cameraIds };
}

const denied = async (method: 'get' | 'post' | 'delete', path: string, account: Account) => {
  const response = await request(baseUrl)[method](path).set(auth(account));
  expect([403, 404]).toContain(response.status);
  return response;
};

(enabled ? describe : describe.skip)('live Phase 11B two-tenant security gate', () => {
  let tenantA: Tenant;
  let tenantB: Tenant;

  beforeAll(async () => {
    tenantA = await createTenant('tenant-a');
    tenantB = await createTenant('tenant-b');
  }, 120000);

  it('creates an authenticated owner organization and rejects duplicate email', async () => {
    const email = uniqueEmail('duplicate');
    const payload = { email, password: 'Phase11B-safe-test-password-123!', organizationName: 'Duplicate test' };
    const first = await request(baseUrl).post('/api/auth/signup').send(payload);
    expect(first.status).toBe(201);
    const duplicate = await request(baseUrl).post('/api/auth/signup').send({ ...payload, organizationName: 'Should not exist' });
    expect(duplicate.status).toBe(409);
    expect(duplicate.body.message).toContain('already registered');
    const organization = await request(baseUrl).get(`/api/organizations/${first.body.user.organizationId}`).set(auth(first.body));
    expect(organization.status).toBe(200);
  });

  it('gives each tenant three slots and returns the typed fourth-camera error', async () => {
    for (const tenant of [tenantA, tenantB]) {
      const response = await request(baseUrl)
        .post('/api/cameras')
        .set(auth(tenant))
        .send({ name: 'over-limit', siteId: tenant.siteId, streamUrl: 'rtsp://safe.example.test/over-limit', protocol: 'rtsp' });
      expect(response.status).toBe(409);
      expect(response.body).toEqual(expect.objectContaining({ code: 'CAMERA_LIMIT_REACHED' }));
      expect(response.body.message).toContain('Please contact us');
      const list = await request(baseUrl).get('/api/cameras').set(auth(tenant));
      expect(list.status).toBe(200);
      expect(list.body).toHaveLength(3);
    }
  });

  it('rejects cross-tenant direct IDs and keeps lists and filters scoped', async () => {
    await expect(request(baseUrl).get(`/api/organizations/${tenantB.user.organizationId}`).set(auth(tenantA))).resolves.toMatchObject({ status: 404 });
    await expect(request(baseUrl).get(`/api/organizations/${tenantB.user.organizationId}/sites`).set(auth(tenantA))).resolves.toMatchObject({ status: 404 });
    await denied('get', `/api/cameras/${tenantB.cameraIds[0]}`, tenantA);
    await denied('get', `/api/cameras/${tenantB.cameraIds[0]}/status`, tenantA);
    const crossTenantSiteCameras = await request(baseUrl).get(`/api/cameras/site/${tenantB.siteId}`).set(auth(tenantA));
    expect(crossTenantSiteCameras.status).toBe(200);
    expect(crossTenantSiteCameras.body).toEqual([]);
    const [aCameras, bCameras] = await Promise.all([
      request(baseUrl).get('/api/cameras').query({ siteId: tenantB.siteId }).set(auth(tenantA)),
      request(baseUrl).get('/api/cameras').set(auth(tenantB)),
    ]);
    expect(aCameras.status).toBe(200);
    expect(aCameras.body.map((camera: { id: string }) => camera.id)).toEqual(expect.arrayContaining(tenantA.cameraIds));
    expect(aCameras.body.map((camera: { id: string }) => camera.id)).not.toEqual(expect.arrayContaining(tenantB.cameraIds));
    expect(bCameras.body.map((camera: { id: string }) => camera.id)).toEqual(expect.arrayContaining(tenantB.cameraIds));
    const dashboard = await request(baseUrl).get('/api/dashboard/stats').set(auth(tenantA));
    expect(dashboard.status).toBe(200);
    expect(JSON.stringify(dashboard.body)).not.toContain(tenantB.cameraIds[0]);
    const analytics = await request(baseUrl).get('/api/analytics/cameras').set(auth(tenantA));
    expect(analytics.status).toBe(200);
  });

  it('does not disclose camera credentials on read or status responses', async () => {
    for (const cameraId of tenantA.cameraIds) {
      for (const path of [`/api/cameras/${cameraId}`, `/api/cameras/${cameraId}/status`]) {
        const response = await request(baseUrl).get(path).set(auth(tenantA));
        expect(response.status).toBe(200);
        expect(JSON.stringify(response.body)).not.toContain('safe-test-camera-password');
        expect(response.body).not.toHaveProperty('passwordEncrypted');
      }
    }
  });

  it('accepts a valid socket token, rejects an invalid one, and isolates organization events', async () => {
    const connect = (token: string) => io(baseUrl, { auth: { token }, transports: ['websocket'], forceNew: true, reconnection: false });
    const makeRule = async (token: string, cameraId: string, name: string) => {
      const response = await request(baseUrl).post('/api/rules').set(auth({ ...tenantA, accessToken: token })).send({
        name,
        ruleType: 'motion',
        status: 'active',
        cameraId,
        severity: 'medium',
        confidenceThreshold: 0.7,
      });
      expect(response.status).toBe(201);
      return response.body;
    };
    const tenantRuleA = await makeRule(tenantA.accessToken, tenantA.cameraIds[0], 'tenant-a-socket-rule');
    const tenantRuleB = await makeRule(tenantB.accessToken, tenantB.cameraIds[0], 'tenant-b-socket-rule');

    const socketA = connect(tenantA.accessToken);
    const socketB = connect(tenantB.accessToken);
    const receivedA: any[] = [];
    const receivedB: any[] = [];
    socketA.on('event.created', (event) => receivedA.push(event));
    socketB.on('event.created', (event) => receivedB.push(event));

    await Promise.all([
      new Promise<void>((resolve, reject) => { socketA.once('connect', () => resolve()); socketA.once('connect_error', reject); }),
      new Promise<void>((resolve, reject) => { socketB.once('connect', () => resolve()); socketB.once('connect_error', reject); }),
    ]);

    const aEvent = await request(baseUrl).post('/api/demo/generate-event').set(auth(tenantA)).send({ cameraId: tenantA.cameraIds[0], ruleId: tenantRuleA.id });
    expect(aEvent.status).toBe(201);
    const bEvent = await request(baseUrl).post('/api/demo/generate-event').set(auth(tenantB)).send({ cameraId: tenantB.cameraIds[0], ruleId: tenantRuleB.id });
    expect(bEvent.status).toBe(201);

    await new Promise((resolve) => setTimeout(resolve, 1500));

    expect(receivedA.some((event) => event.organizationId === tenantA.user.organizationId)).toBe(true);
    expect(receivedA.some((event) => event.organizationId === tenantB.user.organizationId)).toBe(false);
    expect(receivedB.some((event) => event.organizationId === tenantB.user.organizationId)).toBe(true);
    expect(receivedB.some((event) => event.organizationId === tenantA.user.organizationId)).toBe(false);

    const invalidSocket = connect('invalid-token');
    const invalidResult = await new Promise<'connect_error' | 'connect' | 'timeout'>((resolve) => {
      const timeout = setTimeout(() => { invalidSocket.close(); resolve('timeout'); }, 3000);
      invalidSocket.once('connect_error', () => { clearTimeout(timeout); resolve('connect_error'); });
      invalidSocket.once('connect', () => { clearTimeout(timeout); invalidSocket.close(); resolve('connect'); });
    });
    expect(invalidResult).toBe('connect_error');
    socketA.disconnect();
    socketB.disconnect();
    expect(tenantA.user.organizationId).not.toBe(tenantB.user.organizationId);
  });
});