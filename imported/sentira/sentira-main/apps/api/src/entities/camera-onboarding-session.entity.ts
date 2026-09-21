import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { Organization } from './organization.entity';

@Entity('camera_onboarding_sessions')
@Index(['organizationId', 'status'])
@Index(['pairingCodeHash'], { unique: true })
export class CameraOnboardingSession {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ type: 'uuid' }) organizationId: string;
  @ManyToOne(() => Organization, { onDelete: 'CASCADE' }) @JoinColumn({ name: 'organizationId' }) organization: Organization;
  @Column({ type: 'uuid' }) userId: string;
  @Column({ type: 'varchar', length: 32 }) method: 'automatic' | 'qr' | 'dvr_nvr' | 'advanced';
  @Column({ type: 'varchar', length: 32, default: 'waiting_for_connector' }) status: 'waiting_for_connector' | 'waiting_for_pairing' | 'connected' | 'complete' | 'expired';
  @Column({ type: 'text', nullable: true }) pairingCodeHash: string;
  @Column({ type: 'timestamp' }) expiresAt: Date;
  @Column({ type: 'timestamp', nullable: true }) usedAt: Date;
  @Column({ type: 'uuid', nullable: true }) connectorId: string;
  @CreateDateColumn() createdAt: Date;
  @UpdateDateColumn() updatedAt: Date;
}
