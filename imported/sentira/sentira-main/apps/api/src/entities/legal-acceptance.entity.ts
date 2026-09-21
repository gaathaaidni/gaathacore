import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn } from 'typeorm';
import { Organization } from './organization.entity';
import { User } from './user.entity';
import { LegalDocument } from './legal-document.entity';

@Entity('legal_acceptances')
@Index(['userId', 'documentType', 'documentVersion'], { unique: true })
@Index(['organizationId', 'createdAt'])
export class LegalAcceptance {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  userId: string;

  @ManyToOne(() => User, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'userId' })
  user: User;

  @Column({ type: 'uuid' })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'uuid' })
  documentId: string;

  @ManyToOne(() => LegalDocument, { onDelete: 'RESTRICT' })
  @JoinColumn({ name: 'documentId' })
  document: LegalDocument;

  @Column({ type: 'varchar', length: 64 })
  documentType: string;

  @Column({ type: 'varchar', length: 32 })
  documentVersion: string;

  @Column({ type: 'varchar', length: 24 })
  acceptanceType: 'AGREEMENT' | 'ACKNOWLEDGEMENT';

  @Column({ type: 'timestamp', default: () => 'now()' })
  acceptedAt: Date;

  @Column({ type: 'varchar', length: 128, nullable: true })
  ipAddress: string;

  @Column({ type: 'text', nullable: true })
  userAgent: string;

  @Column({ type: 'varchar', length: 32, default: 'WEB' })
  source: string;

  @CreateDateColumn()
  createdAt: Date;
}
