import { ObjectStorageService } from './object-storage.service';

describe('ObjectStorageService', () => {
  const originalFetch = global.fetch;
  const originalEnvironment = { ...process.env };

  beforeEach(() => {
    process.env.MINIO_ENDPOINT = 'minio'; process.env.MINIO_PORT = '9000';
    process.env.MINIO_ACCESS_KEY = 'test-access'; process.env.MINIO_SECRET_KEY = 'test-secret';
  });
  afterEach(() => { global.fetch = originalFetch; process.env = { ...originalEnvironment }; });

  it('initializes its bucket and encodes opaque object-key components', async () => {
    const urls: string[] = [];
    global.fetch = jest.fn(async (input: RequestInfo | URL) => {
      urls.push(String(input));
      return new Response('', { status: urls.length === 1 ? 404 : 200 });
    }) as typeof fetch;
    const storage = new ObjectStorageService();

    await storage.put('organizations/a b/events/id?#/snapshot.jpg', Buffer.from('jpeg'), 'image/jpeg');

    expect(urls).toEqual([
      'http://minio:9000/sentira-evidence',
      'http://minio:9000/sentira-evidence',
      'http://minio:9000/sentira-evidence/organizations/a%20b/events/id%3F%23/snapshot.jpg',
    ]);
  });

  it('rejects keys that escape the tenant namespace', async () => {
    const storage = new ObjectStorageService();

    await expect(storage.getForOrganization('org-a', '../org-b/secret.mp4')).rejects.toThrow('tenant-scoped object key');
  });
});
