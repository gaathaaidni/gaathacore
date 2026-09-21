import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { Organization } from './organization.entity';
import { User } from './user.entity';

export type PrivacyRequestType = 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'RESTRICTION' | 'PORTABILITY' | 'OBJECTION' | 'WITHDRAW_CONSENT' | 'OTHER_PRIVACY_REQUEST';
export type PrivacyRequestStatus = 'SUBMITTED' | 'IDENTITY_REVIEW' | 'IN_REVIEW' | 'PROCESSING' | 'COMPLETED' | 'REJECTED';

@Entity('privacy_requests')
@Index(['organizationId', 'status', 'createdAt'])
export class PrivacyRequest {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid', nullable: true })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'uuid', nullable: true })
  requesterUserId: string;

  @ManyToOne(() => User, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'requesterUserId' })
  requesterUser: User;

  @Column({ type: 'varchar', length: 255 })
  requesterEmail: string;

  @Column({ type: 'varchar', length: 32 })
  requestType: PrivacyRequestType;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ type: 'varchar', length: 32, default: 'SUBMITTED' })
  status: PrivacyRequestStatus;

  @Column({ type: 'timestamp', nullable: true })
  identityVerifiedAt: Date;

  @Column({ type: 'text', nullable: true })
  resolution: string;

  @Column({ type: 'timestamp', nullable: true })
  completedAt: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
