import { LegalService } from './legal.service';

function repo(records: any[] = []) {
  return {
    records,
    find: jest.fn(async ({ where }: any = {}) => records.filter((record) => Object.entries(where || {}).every(([key, value]) => record[key] === value))),
    findOne: jest.fn(async ({ where }: any) => records.find((record) => Object.entries(where || {}).every(([key, value]) => record[key] === value))),
    findOneBy: jest.fn(async (where: any) => records.find((record) => Object.entries(where).every(([key, value]) => record[key] === value))),
    save: jest.fn(async (value: any) => { const saved = { id: value.id || `${records.length + 1}`, createdAt: new Date(), ...value }; if (!value.id) records.push(saved); return saved; }),
  };
}

const user = { id: 'user-1', organizationId: 'org-1' } as any;

describe('LegalService', () => {
  it('returns only published effective documents', async () => {
    const documents = repo([
      { id: 'terms-1', documentType: 'TERMS_OF_SERVICE', version: '1.0', status: 'PUBLISHED', effectiveAt: new Date(Date.now() - 1000) },
      { id: 'draft-1', documentType: 'PRIVACY_POLICY', version: '2.0', status: 'DRAFT', effectiveAt: new Date(Date.now() - 1000) },
      { id: 'future-1', documentType: 'COOKIE_POLICY', version: '2.0', status: 'PUBLISHED', effectiveAt: new Date(Date.now() + 60_000) },
    ]);
    const service = new LegalService(repo() as any, repo() as any, repo() as any, documents as any, repo() as any);
    await expect(service.listPublished()).resolves.toEqual([expect.objectContaining({ id: 'terms-1' })]);
  });

  it('records acceptance once for a document version and never stores cookie session ids', async () => {
    const audits = repo();
    const consents = repo();
    const acceptances = repo();
    const documents = repo([{ id: 'terms-1', documentType: 'TERMS_OF_SERVICE', version: '1.0', status: 'PUBLISHED' }]);
    const service = new LegalService(audits as any, consents as any, acceptances as any, documents as any, repo() as any);

    await service.accept(user, { documentId: 'terms-1', acceptanceType: 'AGREEMENT' }, { ip: '127.0.0.1' });
    await service.accept(user, { documentId: 'terms-1', acceptanceType: 'AGREEMENT' }, {});
    await service.recordCookieConsent({ sessionId: 'session-id-that-must-not-be-stored', categories: { necessary: true } }, {});

    expect(acceptances.records).toHaveLength(1);
    expect(consents.records[0].subjectHash).not.toContain('session-id-that-must-not-be-stored');
    expect(audits.records).toHaveLength(1);
  });

  it('records each accepted document version and keeps prior acceptance immutable', async () => {
    const acceptances = repo();
    const documents = repo([
      { id: 'terms-1', documentType: 'TERMS_OF_SERVICE', version: '1.0', status: 'PUBLISHED' },
      { id: 'terms-2', documentType: 'TERMS_OF_SERVICE', version: '2.0', status: 'PUBLISHED' },
    ]);
    const service = new LegalService(repo() as any, repo() as any, acceptances as any, documents as any, repo() as any);

    const first = await service.accept(user, { documentId: 'terms-1', acceptanceType: 'AGREEMENT' }, {});
    const second = await service.accept(user, { documentId: 'terms-2', acceptanceType: 'AGREEMENT' }, {});
    const repeated = await service.accept(user, { documentId: 'terms-1', acceptanceType: 'AGREEMENT' }, {});

    expect(acceptances.records).toHaveLength(2);
    expect(first).toEqual(expect.objectContaining({ documentId: 'terms-1', documentVersion: '1.0' }));
    expect(second).toEqual(expect.objectContaining({ documentId: 'terms-2', documentVersion: '2.0' }));
    expect(repeated).toBe(first);
    expect(first.documentVersion).toBe('1.0');
  });

  it('never publishes a document with missing configuration or unresolved placeholders', async () => {
    const documents = repo([
      { id: 'draft-1', documentType: 'TERMS_OF_SERVICE', version: '1.0', title: 'Terms', content: 'Final [GOVERNING_LAW]', jurisdiction: 'EU', language: 'en', status: 'DRAFT' },
    ]);
    const service = new LegalService(repo() as any, repo() as any, repo() as any, documents as any, repo() as any);

    await expect(service.publishDocument('draft-1', { status: 'PUBLISHED' }, user)).rejects.toThrow();
    expect(documents.records[0].status).toBe('DRAFT');
  });

  it('keeps marketing consent independent and scopes privacy requests to the tenant', async () => {
    const audits = repo();
    const consents = repo();
    const requests = repo();
    const service = new LegalService(audits as any, consents as any, repo() as any, repo() as any, requests as any);

    await service.recordMarketingConsent(user, { granted: false });
    const request = await service.createPrivacyRequest(user, { requestType: 'ACCESS', requesterEmail: 'person@example.com', description: 'Please review my request.' });

    expect(consents.records[0]).toEqual(expect.objectContaining({ consentType: 'MARKETING', userId: 'user-1', organizationId: 'org-1', withdrawnAt: expect.any(Date) }));
    expect(request).toEqual(expect.objectContaining({ status: 'SUBMITTED' }));
    expect(requests.records[0].organizationId).toBe('org-1');
    expect(audits.records).toHaveLength(2);

    requests.records.push({ id: 'other-org', organizationId: 'org-2', createdAt: new Date() });
    await expect(service.listPrivacyRequests(user)).resolves.toEqual([expect.objectContaining({ organizationId: 'org-1' })]);
  });
});
