import { CCTV_GUIDES, CCTV_MANUFACTURERS, CCTV_MODELS, seedCctvCatalog } from './catalog';

function repository<T extends { id: string }>() {
  const records: T[] = [];
  return {
    records,
    findOne: jest.fn(async ({ where }: { where: Record<string, unknown> }) => records.find((record) =>
      Object.entries(where).every(([key, value]) => (record as any)[key] === value))),
    save: jest.fn(async (record: T) => {
      const saved = { ...record, id: record.id || `${records.length + 1}` } as T;
      records.push(saved);
      return saved;
    }),
  };
}

describe('CCTV catalog seed', () => {
  it('seeds manufacturers, related models and guides idempotently', async () => {
    const manufacturers = repository<any>();
    const models = repository<any>();
    const guides = repository<any>();

    const first = await seedCctvCatalog(manufacturers as any, models as any, guides as any);
    const second = await seedCctvCatalog(manufacturers as any, models as any, guides as any);

    expect(first).toEqual({ manufacturers: CCTV_MANUFACTURERS.length, models: CCTV_MODELS.length, guides: CCTV_GUIDES.length });
    expect(second).toEqual(first);
    expect(manufacturers.records).toHaveLength(CCTV_MANUFACTURERS.length);
    expect(models.records).toHaveLength(CCTV_MODELS.length);
    expect(guides.records).toHaveLength(CCTV_GUIDES.length);
    expect(new Set(manufacturers.records.map((record) => record.slug)).size).toBe(CCTV_MANUFACTURERS.length);
    expect(models.records.every((record) => manufacturers.records.some((manufacturer) => manufacturer.id === record.manufacturerId))).toBe(true);
    expect(guides.records.some((record) => record.title === 'Connect a Generic ONVIF Camera')).toBe(true);
    expect(guides.records.some((record) => record.title === 'Connect a Generic RTSP Camera')).toBe(true);
    expect(guides.records.some((record) => record.title === 'Connect an NVR, DVR or XVR Recorder')).toBe(true);
  });
});
