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

@Entity('cameras')
@Index(['organizationId', 'siteId', 'name'])
@Index(['status'])
export class Camera {
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

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  location: string;

  @Column({ type: 'text', nullable: true, comment: 'Stream URL without credentials; connector cameras may not have a cloud URL' })
  streamUrl: string;

  @Column({ type: 'varchar', length: 32, default: 'manual' })
  sourceType: 'manual' | 'connector' | 'qr' | 'dvr_nvr';

  @Column({ type: 'uuid', nullable: true })
  connectorId: string;

  @Column({ type: 'uuid', nullable: true })
  discoveredCameraId: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  username: string;

  @Column({ type: 'text', nullable: true, comment: 'Encrypted password' })
  passwordEncrypted: string;

  @Column({ type: 'varchar', length: 50 })
  protocol: 'rtsp' | 'http' | 'https' | 'connector';

  @Column({ type: 'varchar', length: 50, default: 'offline' })
  status: 'online' | 'offline' | 'connecting' | 'error' | 'ai_processing' | 'disabled';

  @Column({ type: 'varchar', length: 100, nullable: true })
  resolution: string;

  @Column({ type: 'integer', default: 30 })
  fps: number;

  @Column({ type: 'timestamp', nullable: true })
  lastHeartbeatAt: Date;

  @Column({ type: 'varchar', length: 50, default: 'idle' })
  aiProcessingStatus: 'idle' | 'processing' | 'error';

  @Column({ type: 'boolean', default: true })
  isEnabled: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
