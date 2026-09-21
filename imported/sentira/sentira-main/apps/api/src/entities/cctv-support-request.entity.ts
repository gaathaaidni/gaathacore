import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('cctv_support_requests')
@Index(['organizationId', 'status'])
export class CctvSupportRequest {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @Column({ type: 'uuid' })
  userId: string;

  @Column({ type: 'uuid', nullable: true })
  setupSessionId: string;

  @Column({ type: 'uuid', nullable: true })
  siteId: string;

  @Column({ type: 'uuid', nullable: true })
  cameraId: string;

  @Column({ type: 'varchar', length: 32, default: 'OPEN' })
  status: 'OPEN' | 'TRIAGED' | 'IN_PROGRESS' | 'WAITING_FOR_CUSTOMER' | 'RESOLVED' | 'CLOSED';

  @Column({ type: 'varchar', length: 16, default: 'NORMAL' })
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL';

  @Column({ type: 'varchar', length: 40 })
  reason: 'SETUP_HELP' | 'CAMERA_INCOMPATIBILITY' | 'DVR_SETUP' | 'NVR_SETUP' | 'NETWORK_ISSUE' | 'AUTHENTICATION' | 'STREAM_ISSUE' | 'DISCOVERY_FAILURE' | 'OTHER';

  @Column({ type: 'text', nullable: true })
  message: string;

  @Column({ type: 'jsonb', default: '{}' })
  context: Record<string, unknown>;

  @Column({ type: 'uuid', nullable: true })
  assignedTo: string;

  @Column({ type: 'text', nullable: true })
  resolution: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
