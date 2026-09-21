import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('cctv_setup_sessions')
@Index(['organizationId', 'status'])
export class CctvSetupSession {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @Column({ type: 'uuid' })
  userId: string;

  @Column({ type: 'uuid', nullable: true })
  siteId: string;

  @Column({ type: 'varchar', length: 40, nullable: true })
  deviceType: string;

  @Column({ type: 'uuid', nullable: true })
  manufacturerId: string;

  @Column({ type: 'uuid', nullable: true })
  modelId: string;

  @Column({ type: 'uuid', nullable: true })
  guideId: string;

  @Column({ type: 'uuid', nullable: true })
  connectorId: string;

  @Column({ type: 'text', nullable: true })
  pairingCodeHash: string;

  @Column({ type: 'timestamp', nullable: true })
  pairingExpiresAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  pairingUsedAt: Date;

  @Column({ type: 'varchar', length: 32, default: 'STARTED' })
  status: 'STARTED' | 'IN_PROGRESS' | 'PAUSED' | 'TESTING' | 'VERIFIED' | 'COMPLETED' | 'FAILED' | 'SUPPORT_REQUESTED';

  @Column({ type: 'varchar', length: 32, default: 'IDENTIFY' })
  stage: 'IDENTIFY' | 'FIND' | 'CONNECT' | 'TEST' | 'FINISH';

  @Column({ type: 'varchar', length: 120, nullable: true })
  currentStep: string;

  @Column({ type: 'integer', default: 0 })
  completionPercent: number;

  @Column({ type: 'jsonb', default: '{}' })
  answers: Record<string, unknown>;

  @Column({ type: 'jsonb', nullable: true })
  testResult: Record<string, unknown>;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
