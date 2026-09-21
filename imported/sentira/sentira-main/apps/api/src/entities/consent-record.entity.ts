import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn } from 'typeorm';
import { Organization } from './organization.entity';
import { User } from './user.entity';

export type ConsentType = 'COOKIE' | 'MARKETING';

@Entity('consent_records')
@Index(['subjectHash', 'consentType', 'createdAt'])
@Index(['organizationId', 'consentType', 'createdAt'])
export class ConsentRecord {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 24 })
  consentType: ConsentType;

  @Column({ type: 'uuid', nullable: true })
  userId: string;

  @ManyToOne(() => User, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'userId' })
  user: User;

  @Column({ type: 'uuid', nullable: true })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'varchar', length: 128, nullable: true })
  subjectHash: string;

  @Column({ type: 'jsonb', default: '{}' })
  categories: Record<string, boolean>;

  @Column({ type: 'varchar', length: 32, nullable: true })
  policyVersion: string;

  @Column({ type: 'varchar', length: 32, nullable: true })
  cookiePolicyVersion: string;

  @Column({ type: 'varchar', length: 32, default: 'WEB' })
  source: string;

  @Column({ type: 'timestamp', nullable: true })
  withdrawnAt: Date;

  @CreateDateColumn()
  createdAt: Date;
}
