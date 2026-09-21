import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

export type LegalDocumentType =
  | 'TERMS_OF_SERVICE'
  | 'PRIVACY_POLICY'
  | 'COOKIE_POLICY'
  | 'ACCEPTABLE_USE_POLICY'
  | 'AI_TRANSPARENCY_NOTICE'
  | 'VIDEO_SURVEILLANCE_NOTICE'
  | 'DATA_PROCESSING_AGREEMENT'
  | 'SUBPROCESSOR_LIST'
  | 'DATA_RETENTION_POLICY'
  | 'SECURITY_POLICY'
  | 'ACCOUNT_DELETION_POLICY'
  | 'SECURITY_INCIDENT_POLICY';
export type LegalDocumentStatus = 'DRAFT' | 'IN_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED';

@Entity('legal_documents')
@Index(['documentType', 'version'], { unique: true })
@Index(['documentType', 'status', 'effectiveAt'])
export class LegalDocument {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 64 })
  documentType: LegalDocumentType;

  @Column({ type: 'varchar', length: 32 })
  version: string;

  @Column({ type: 'varchar', length: 240 })
  title: string;

  @Column({ type: 'text' })
  content: string;

  @Column({ type: 'timestamp', nullable: true })
  effectiveAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  publishedAt: Date;

  @Column({ type: 'varchar', length: 24, default: 'DRAFT' })
  status: LegalDocumentStatus;

  @Column({ type: 'varchar', length: 64, default: 'GLOBAL' })
  jurisdiction: string;

  @Column({ type: 'varchar', length: 16, default: 'en' })
  language: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
