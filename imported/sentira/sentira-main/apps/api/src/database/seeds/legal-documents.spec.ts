import { LEGAL_DOCUMENTS, seedLegalDocuments } from './legal-documents';

describe('legal document seed', () => {
  it('creates only unpublished drafts, including when draft text contains placeholders', async () => {
    const records: any[] = [];
    const repository: any = {
      findOne: jest.fn(async ({ where }: any) => records.find((record) => record.documentType === where.documentType && record.version === where.version)),
      save: jest.fn(async (document: any) => { const saved = { id: `${records.length + 1}`, ...document }; records.push(saved); return saved; }),
    };

    await seedLegalDocuments(repository);

    expect(records).toHaveLength(LEGAL_DOCUMENTS.length);
    expect(records.every((record) => record.status === 'DRAFT')).toBe(true);
    expect(records.every((record) => !record.publishedAt && !record.effectiveAt)).toBe(true);
    expect(records.some((record) => record.content.includes('[EFFECTIVE_DATE]'))).toBe(true);

    await seedLegalDocuments(repository);
    expect(records).toHaveLength(LEGAL_DOCUMENTS.length);
  });
});