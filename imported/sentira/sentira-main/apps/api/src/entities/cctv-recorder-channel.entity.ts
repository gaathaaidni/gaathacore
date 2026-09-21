import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('cctv_recorder_channels')
@Index(['recorderId', 'channelNumber'], { unique: true })
export class CctvRecorderChannel {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ type: 'uuid' }) recorderId: string;
  @Column({ type: 'uuid' }) organizationId: string;
  @Column({ type: 'integer' }) channelNumber: number;
  @Column({ type: 'varchar', length: 255, nullable: true }) name: string;
  @Column({ type: 'boolean', default: false }) available: boolean;
  @Column({ type: 'varchar', length: 20, nullable: true }) protocol: string;
  @Column({ type: 'boolean', default: false }) streamAvailable: boolean;
  @Column({ type: 'varchar', length: 32, default: 'UNAVAILABLE' }) verificationStatus: 'VERIFIED' | 'UNVERIFIED' | 'UNAVAILABLE';
  @Column({ type: 'uuid', nullable: true }) cameraId: string;
  @Column({ type: 'jsonb', default: '{}' }) metadata: Record<string, unknown>;
  @CreateDateColumn() createdAt: Date;
  @UpdateDateColumn() updatedAt: Date;
}
