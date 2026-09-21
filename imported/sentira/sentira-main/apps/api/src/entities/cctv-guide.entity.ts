import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { CctvManufacturer } from './cctv-manufacturer.entity';
import { CctvModel } from './cctv-model.entity';

export type CctvGuideStepType = 'TEXT' | 'IMAGE' | 'VIDEO' | 'WARNING' | 'TIP' | 'INPUT' | 'CHOICE' | 'TEST' | 'SUCCESS' | 'FAILURE';

@Entity('cctv_setup_guides')
@Index(['manufacturerId', 'modelId', 'active'])
export class CctvSetupGuide {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid', nullable: true })
  manufacturerId: string;

  @ManyToOne(() => CctvManufacturer, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'manufacturerId' })
  manufacturer: CctvManufacturer;

  @Column({ type: 'uuid', nullable: true })
  modelId: string;

  @ManyToOne(() => CctvModel, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'modelId' })
  model: CctvModel;

  @Column({ type: 'varchar', length: 180 })
  title: string;

  @Column({ type: 'text' })
  description: string;

  @Column({ type: 'varchar', length: 32, default: 'beginner' })
  difficulty: string;

  @Column({ type: 'integer', default: 15 })
  estimatedMinutes: number;

  @Column({ type: 'jsonb', default: '[]' })
  prerequisites: string[];

  @Column({ type: 'jsonb', default: '[]' })
  steps: Array<{ id: string; type: CctvGuideStepType; title: string; body: string; choices?: Array<{ label: string; value: string; nextStepId?: string }>; required?: boolean }>;

  @Column({ type: 'jsonb', default: '[]' })
  troubleshooting: Array<{ condition: string; advice: string; guideStepId?: string }>;

  @Column({ type: 'varchar', length: 80, default: 'unverified' })
  verificationStatus: 'unverified' | 'verified' | 'outdated';

  @Column({ type: 'timestamp', nullable: true })
  lastVerifiedAt: Date;

  @Column({ type: 'integer', default: 1 })
  version: number;

  @Column({ type: 'boolean', default: true })
  active: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
