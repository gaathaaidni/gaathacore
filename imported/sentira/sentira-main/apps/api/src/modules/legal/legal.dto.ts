import { IsBoolean, IsEmail, IsIn, IsObject, IsOptional, IsString, IsUUID, MaxLength, MinLength } from 'class-validator';
import { LegalDocumentType } from '../../entities/legal-document.entity';
import { PrivacyRequestType } from '../../entities/privacy-request.entity';

export class AcceptLegalDocumentDto {
  @IsUUID()
  documentId: string;

  @IsIn(['AGREEMENT', 'ACKNOWLEDGEMENT'])
  acceptanceType: 'AGREEMENT' | 'ACKNOWLEDGEMENT';
}

export class CookieConsentDto {
  @IsString()
  @MinLength(16)
  @MaxLength(128)
  sessionId: string;

  @IsObject()
  categories: Record<string, boolean>;

  @IsOptional()
  @IsString()
  @MaxLength(32)
  cookiePolicyVersion?: string;
}

export class MarketingConsentDto {
  @IsBoolean()
  granted: boolean;
}

export class PrivacyRequestDto {
  @IsIn(['ACCESS', 'RECTIFICATION', 'ERASURE', 'RESTRICTION', 'PORTABILITY', 'OBJECTION', 'WITHDRAW_CONSENT', 'OTHER_PRIVACY_REQUEST'] satisfies PrivacyRequestType[])
  requestType: PrivacyRequestType;

  @IsEmail()
  requesterEmail: string;

  @IsOptional()
  @IsString()
  @MaxLength(5000)
  description?: string;
}

export class PublishLegalDocumentDto {
  @IsIn(['DRAFT', 'IN_REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED'])
  status: 'DRAFT' | 'IN_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED';
}

export class CreateLegalDocumentDto {
  @IsIn(['TERMS_OF_SERVICE', 'PRIVACY_POLICY', 'COOKIE_POLICY', 'ACCEPTABLE_USE_POLICY', 'AI_TRANSPARENCY_NOTICE', 'VIDEO_SURVEILLANCE_NOTICE', 'DATA_PROCESSING_AGREEMENT', 'SUBPROCESSOR_LIST', 'DATA_RETENTION_POLICY', 'SECURITY_POLICY', 'ACCOUNT_DELETION_POLICY', 'SECURITY_INCIDENT_POLICY'] satisfies LegalDocumentType[])
  documentType: LegalDocumentType;

  @IsString()
  @MaxLength(32)
  version: string;

  @IsString()
  @MaxLength(240)
  title: string;

  @IsString()
  content: string;

  @IsOptional()
  @IsString()
  @MaxLength(64)
  jurisdiction?: string;

  @IsOptional()
  @IsString()
  @MaxLength(16)
  language?: string;
}

export class UpdatePrivacyRequestDto {
  @IsIn(['SUBMITTED', 'IDENTITY_REVIEW', 'IN_REVIEW', 'PROCESSING', 'COMPLETED', 'REJECTED'])
  status: 'SUBMITTED' | 'IDENTITY_REVIEW' | 'IN_REVIEW' | 'PROCESSING' | 'COMPLETED' | 'REJECTED';

  @IsOptional()
  @IsString()
  @MaxLength(5000)
  resolution?: string;
}
