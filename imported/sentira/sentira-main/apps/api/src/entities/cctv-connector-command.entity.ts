import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { Connector } from './connector.entity';
import { Organization } from './organization.entity';

@Entity('cctv_connector_commands')
@Index(['organizationId', 'status', 'createdAt'])
@Index(['connectorId', 'status', 'expiresAt'])
@Index(['correlationId'])
@Index(['idempotencyKey'], { unique: true, where: '"idempotencyKey" IS NOT NULL' })
export class CctvConnectorCommand {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'uuid' })
  connectorId: string;

  @ManyToOne(() => Connector, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'connectorId' })
  connector: Connector;

  @Column({ type: 'varchar', length: 40 })
  commandType: 'PING' | 'GET_CAPABILITIES' | 'DISCOVER_ONVIF' | 'GET_ONVIF_DEVICE_INFORMATION' | 'GET_ONVIF_MEDIA_PROFILES' | 'GET_ONVIF_STREAM_URI' | 'VERIFY_ONVIF_DEVICE' | 'TEST_RTSP';

  @Column({ type: 'varchar', length: 32, default: 'QUEUED' })
  status: 'QUEUED' | 'DELIVERED' | 'ACKNOWLEDGED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMEOUT' | 'CANCELLED' | 'EXPIRED';

  @Column({ type: 'jsonb', default: {} })
  payload: Record<string, unknown>;

  @Column({ type: 'jsonb', default: {} })
  result: Record<string, unknown>;

  @Column({ type: 'varchar', length: 80, nullable: true })
  errorCode: string | null;

  @Column({ type: 'text', nullable: true })
  errorMessage: string | null;

  @CreateDateColumn()
  createdAt: Date;

  @Column({ type: 'timestamp', nullable: true })
  queuedAt: Date | null;

  @Column({ type: 'timestamp', nullable: true })
  startedAt: Date | null;

  @Column({ type: 'timestamp', nullable: true })
  completedAt: Date | null;

  @Column({ type: 'timestamp', nullable: true })
  expiresAt: Date | null;

  @Column({ type: 'int', default: 0 })
  attemptCount: number;

  @Column({ type: 'int', default: 1 })
  maxAttempts: number;

  @Column({ type: 'varchar', length: 64, nullable: true })
  correlationId: string | null;

  @Column({ type: 'text', nullable: true })
  idempotencyKey: string | null;

  @Column({ type: 'int', default: 1 })
  commandVersion: number;

  @Column({ type: 'timestamp', nullable: true })
  leaseUntil: Date | null;

  @UpdateDateColumn()
  updatedAt: Date;
}
