import { createHash } from 'crypto';
import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AuditLog, ConsentRecord, LegalAcceptance, LegalDocument, PrivacyRequest } from '../../entities';
import { CurrentUserDto } from '../../auth/auth.dto';
import { AcceptLegalDocumentDto, CookieConsentDto, CreateLegalDocumentDto, MarketingConsentDto, PrivacyRequestDto, PublishLegalDocumentDto, UpdatePrivacyRequestDto } from './legal.dto';
import { hasCompleteLegalConfig, REQUIRED_LEGAL_PLACEHOLDERS } from '../../config/legal.config';

@Injectable()
export class LegalService {
  constructor(
    @InjectRepository(AuditLog) private readonly audit: Repository<AuditLog>,
    @InjectRepository(ConsentRecord) private readonly consents: Repository<ConsentRecord>,
    @InjectRepository(LegalAcceptance) private readonly acceptances: Repository<LegalAcceptance>,
    @InjectRepository(LegalDocument) private readonly documents: Repository<LegalDocument>,
    @InjectRepository(PrivacyRequest) private readonly requests: Repository<PrivacyRequest>,
  ) {}

  async listPublished(documentType?: string) {
    const documents = await this.documents.find({ where: { status: 'PUBLISHED' }, order: { documentType: 'ASC', version: 'DESC' } });
    const now = Date.now();
    return documents.filter((document) => (!documentType || document.documentType === documentType) && (!document.effectiveAt || document.effectiveAt.getTime() <= now));
  }

  async getPublished(documentType: string) {
    const documents = await this.listPublished(documentType);
    const document = documents[0];
    if (!document) throw new NotFoundException('Published legal document not found');
    return document;
  }

  async listAllDocuments() {
    return this.documents.find({ order: { documentType: 'ASC', version: 'DESC' } });
  }

  async publishDocument(id: string, dto: PublishLegalDocumentDto, user: CurrentUserDto) {
    const document = await this.documents.findOneBy({ id });
    if (!document) throw new NotFoundException('Legal document not found');
    if (dto.status === 'PUBLISHED') this.assertPublishable(document);
    document.status = dto.status;
    document.publishedAt = dto.status === 'PUBLISHED' ? new Date() : document.publishedAt;
    if (dto.status === 'PUBLISHED' && !document.effectiveAt) document.effectiveAt = new Date();
    const saved = await this.documents.save(document);
    await this.writeAudit(user, dto.status === 'PUBLISHED' ? 'LEGAL_DOCUMENT_PUBLISHED' : 'LEGAL_DOCUMENT_STATUS_UPDATED', saved.id, { documentType: saved.documentType, version: saved.version, status: saved.status });
    return saved;
  }

  async createDocument(dto: CreateLegalDocumentDto, user: CurrentUserDto) {
    const document = await this.documents.save({ ...dto, status: 'DRAFT', jurisdiction: dto.jurisdiction || 'GLOBAL', language: dto.language || 'en' });
    await this.writeAudit(user, 'LEGAL_DOCUMENT_CREATED', document.id, { documentType: document.documentType, version: document.version });
    return document;
  }

  async accept(user: CurrentUserDto, dto: AcceptLegalDocumentDto, metadata: { ip?: string; userAgent?: string }) {
    const document = await this.documents.findOne({ where: { id: dto.documentId, status: 'PUBLISHED' } });
    if (!document) throw new NotFoundException('Published legal document not found');
    const existing = await this.acceptances.findOne({ where: { userId: user.id, documentType: document.documentType, documentVersion: document.version } });
    if (existing) return existing;
    const acceptance = await this.acceptances.save({ userId: user.id, organizationId: user.organizationId, documentId: document.id, documentType: document.documentType, documentVersion: document.version, acceptanceType: dto.acceptanceType, ipAddress: metadata.ip, userAgent: metadata.userAgent, source: 'WEB' });
    await this.writeAudit(user, 'LEGAL_DOCUMENT_ACCEPTED', acceptance.id, { documentType: document.documentType, documentVersion: document.version, acceptanceType: dto.acceptanceType });
    return acceptance;
  }

  listAcceptances(user: CurrentUserDto) {
    return this.acceptances.find({ where: { userId: user.id, organizationId: user.organizationId }, order: { createdAt: 'DESC' } });
  }

  async recordCookieConsent(dto: CookieConsentDto, metadata: { ip?: string }) {
    const categories = { necessary: true, preferences: Boolean(dto.categories.preferences), analytics: Boolean(dto.categories.analytics), marketing: Boolean(dto.categories.marketing) };
    const record = await this.consents.save({ consentType: 'COOKIE', subjectHash: this.hash(dto.sessionId), categories, cookiePolicyVersion: dto.cookiePolicyVersion, source: 'WEB', withdrawnAt: categories.preferences || categories.analytics || categories.marketing ? null : new Date() });
    return { id: record.id, recordedAt: record.createdAt };
  }

  async recordMarketingConsent(user: CurrentUserDto, dto: MarketingConsentDto) {
    const record = await this.consents.save({ consentType: 'MARKETING', userId: user.id, organizationId: user.organizationId, categories: { marketing: dto.granted }, source: 'WEB', withdrawnAt: dto.granted ? null : new Date() });
    await this.writeAudit(user, dto.granted ? 'MARKETING_CONSENT_GRANTED' : 'MARKETING_CONSENT_WITHDRAWN', record.id, { granted: dto.granted });
    return { id: record.id, granted: dto.granted, recordedAt: record.createdAt };
  }

  async createPrivacyRequest(user: CurrentUserDto, dto: PrivacyRequestDto) {
    const request = await this.requests.save({ organizationId: user?.organizationId, requesterUserId: user?.id, requesterEmail: dto.requesterEmail.trim().toLowerCase(), requestType: dto.requestType, description: dto.description, status: 'SUBMITTED' });
    if (user) await this.writeAudit(user, 'PRIVACY_REQUEST_CREATED', request.id, { requestType: request.requestType });
    return { id: request.id, status: request.status, createdAt: request.createdAt };
  }

  listPrivacyRequests(user: CurrentUserDto) {
    return this.requests.find({ where: { organizationId: user.organizationId }, order: { createdAt: 'DESC' } });
  }

  async updatePrivacyRequest(id: string, user: CurrentUserDto, dto: UpdatePrivacyRequestDto) {
    const request = await this.requests.findOne({ where: { id, organizationId: user.organizationId } });
    if (!request) throw new NotFoundException('Privacy request not found');
    request.status = dto.status;
    request.resolution = dto.resolution;
    if (dto.status === 'COMPLETED') request.completedAt = new Date();
    const saved = await this.requests.save(request);
    await this.writeAudit(user, 'PRIVACY_REQUEST_STATUS_UPDATED', saved.id, { status: saved.status });
    return saved;
  }

  private hash(value: string) { return createHash('sha256').update(value, 'utf8').digest('hex'); }

  private assertPublishable(document: LegalDocument) {
    if (!hasCompleteLegalConfig() || !document.version?.trim() || !document.title?.trim() || !document.content?.trim() || !document.jurisdiction?.trim() || document.jurisdiction === 'GLOBAL' || !document.language?.trim()) {
      throw new BadRequestException('Legal configuration and document metadata must be complete before publication');
    }
    if (REQUIRED_LEGAL_PLACEHOLDERS.some((placeholder) => document.content.includes(placeholder) || document.title.includes(placeholder))) {
      throw new BadRequestException('Legal document contains unresolved placeholders');
    }
  }

  private async writeAudit(user: CurrentUserDto, action: string, resourceId: string, newValueJson: Record<string, unknown>) {
    await this.audit.save({ organizationId: user.organizationId, userId: user.id, action, resourceType: 'legal', resourceId, newValueJson });
  }
}
