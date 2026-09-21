import {
  Column,
  CreateDateColumn,
  Entity,
  ManyToOne,
  OneToMany,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
  JoinColumn,
  Index,
} from 'typeorm';

import { Organization } from './organization.entity';
import { Site } from './site.entity';
import { Camera } from './camera.entity';
import { RuleCondition } from './rule-condition.entity';
import { RuleAction } from './rule-action.entity';

@Entity('rules')
@Index(['organizationId', 'siteId', 'status'])
@Index(['isActive'])
export class Rule {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'uuid', nullable: true })
  siteId: string;

  @ManyToOne(() => Site, { onDelete: 'CASCADE', nullable: true })
  @JoinColumn({ name: 'siteId' })
  site: Site;

  @Column({ type: 'uuid', nullable: true })
  cameraId: string;

  @ManyToOne(() => Camera, { onDelete: 'CASCADE', nullable: true })
  @JoinColumn({ name: 'cameraId' })
  camera: Camera;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'varchar', length: 1000, nullable: true })
  description: string;

  @Column({ type: 'varchar', length: 100 })
  ruleType: string;

  @Column({ type: 'varchar', length: 50, default: 'active' })
  status: 'active' | 'inactive' | 'archived';

  @Column({ type: 'jsonb', nullable: true })
  scheduleJson: Record<string, unknown>;

  @Column({ type: 'jsonb', nullable: true })
  definitionJson: Record<string, unknown>;

  @Column({ type: 'integer', default: 60 })
  cooldownSeconds: number;

  @Column({ type: 'integer', default: 10 })
  duplicateWindowSeconds: number;

  @Column({ type: 'varchar', length: 50, default: 'medium' })
  severity: 'low' | 'medium' | 'high' | 'critical';

  @Column({ type: 'integer', default: 1 })
  version: number;

  @Column({ type: 'numeric', default: 0.7 })
  confidenceThreshold: number;

  @Column({ type: 'boolean', default: true })
  isActive: boolean;

  @OneToMany(() => RuleCondition, (condition) => condition.rule, { cascade: true })
  conditions: RuleCondition[];

  @OneToMany(() => RuleAction, (action) => action.rule, { cascade: true })
  actions: RuleAction[];

  @Column({ type: 'uuid', nullable: true })
  createdBy: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
