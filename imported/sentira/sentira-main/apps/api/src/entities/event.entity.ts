import {
  Column,
  CreateDateColumn,
  Entity,
  ManyToOne,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
  JoinColumn,
  Index,
} from 'typeorm';

import { Organization } from './organization.entity';
import { Site } from './site.entity';
import { Camera } from './camera.entity';
import { Rule } from './rule.entity';
import { User } from './user.entity';
import { Zone } from './zone.entity';

@Entity('events')
@Index(['organizationId', 'siteId', 'cameraId', 'createdAt'])
@Index(['status', 'severity'])
@Index(['eventType', 'createdAt'])
@Index(['organizationId', 'status', 'createdAt'])
export class Event {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'uuid' })
  siteId: string;

  @ManyToOne(() => Site, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'siteId' })
  site: Site;

  @Column({ type: 'uuid' })
  cameraId: string;

  @ManyToOne(() => Camera, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'cameraId' })
  camera: Camera;

  @Column({ type: 'uuid', nullable: true })
  ruleId: string;

  @ManyToOne(() => Rule, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'ruleId' })
  rule: Rule;

  @Column({ type: 'uuid', nullable: true })
  zoneId: string;

  @ManyToOne(() => Zone, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'zoneId' })
  zone: Zone;

  @Column({ type: 'varchar', length: 255 })
  eventType: string;

  @Column({ type: 'varchar', length: 50, default: 'medium' })
  severity: 'low' | 'medium' | 'high' | 'critical';

  @Column({ type: 'varchar', length: 50, default: 'medium' })
  priority: 'low' | 'medium' | 'high' | 'critical';

  @Column({ type: 'varchar', length: 50, default: 'new' })
  status: 'new' | 'acknowledged' | 'investigating' | 'escalated' | 'resolved' | 'dismissed' | 'false_positive';

  @Column({ type: 'numeric', nullable: true })
  confidence: number;

  @Column({ type: 'varchar', length: 1000, nullable: true })
  description: string;

  @Column({ type: 'integer', nullable: true })
  durationSeconds: number;

  @Column({ type: 'timestamptz', nullable: true })
  firstDetectedAt: Date;

  @Column({ type: 'timestamptz', nullable: true })
  lastDetectedAt: Date;

  @Column({ type: 'varchar', length: 128, nullable: true })
  trackId: string;

  @Column({ type: 'integer', default: 1 })
  ruleVersion: number;

  @Column({ type: 'varchar', length: 128, nullable: true })
  model: string;

  @Column({ type: 'varchar', length: 128, nullable: true })
  modelVersion: string;

  @Column({ type: 'varchar', length: 50, default: 'pending' })
  evidenceStatus: 'pending' | 'processing' | 'ready' | 'failed';

  @Column({ type: 'varchar', length: 500, nullable: true })
  snapshotUrl: string;

  @Column({ type: 'varchar', length: 500, nullable: true })
  videoClipUrl: string;

  @Column({ type: 'text', nullable: true })
  notes: string;

  @Column({ type: 'text', nullable: true }) operatorNotes: string;
  @Column({ type: 'text', nullable: true }) internalComments: string;
  @Column({ type: 'varchar', length: 255, nullable: true }) resolutionReason: string;
  @Column({ type: 'varchar', length: 255, nullable: true }) falsePositiveReason: string;
  @Column({ type: 'varchar', length: 255, nullable: true }) escalationReason: string;
  @Column({ type: 'uuid', nullable: true }) assignedTeamId: string;
  @Column({ type: 'timestamptz', nullable: true }) acknowledgedAt: Date;
  @Column({ type: 'timestamptz', nullable: true }) investigatingAt: Date;
  @Column({ type: 'timestamptz', nullable: true }) escalatedAt: Date;
  @Column({ type: 'timestamptz', nullable: true }) resolvedAt: Date;
  @Column({ type: 'timestamptz', nullable: true }) slaDueAt: Date;
  @Column({ type: 'varchar', length: 20, default: 'on_track' }) slaState: 'on_track' | 'warning' | 'breached';
  @Column({ type: 'timestamptz', nullable: true }) slaBreachedAt: Date;
  @Column({ type: 'uuid', array: true, default: '{}' }) relatedEventIds: string[];
  @Column({ type: 'varchar', length: 100, nullable: true }) correlationId: string;

  @Column({ type: 'uuid', nullable: true })
  assignedUserId: string;

  @ManyToOne(() => User, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'assignedUserId' })
  assignedUser: User;

  @Column({ type: 'uuid', nullable: true })
  acknowledgedByUserId: string;

  @Column({ type: 'uuid', nullable: true })
  resolvedByUserId: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
