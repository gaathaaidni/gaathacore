import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('cctv_recorders')
@Index(['organizationId', 'connectorId'])
export class CctvRecorder {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ type: 'uuid' }) organizationId: string;
  @Column({ type: 'uuid' }) connectorId: string;
  @Column({ type: 'uuid', nullable: true }) setupSessionId: string;
  @Column({ type: 'varchar', length: 255 }) name: string;
  @Column({ type: 'varchar', length: 100, nullable: true }) manufacturer: string;
  @Column({ type: 'varchar', length: 100, nullable: true }) model: string;
  @Column({ type: 'varchar', length: 32 }) deviceType: 'DVR' | 'NVR' | 'XVR';
  @Column({ type: 'varchar', length: 32, default: 'DISCOVERED' }) status: 'DISCOVERED' | 'VERIFIED' | 'UNAVAILABLE';
  @Column({ type: 'jsonb', default: '{}' }) metadata: Record<string, unknown>;
  @CreateDateColumn() createdAt: Date;
  @UpdateDateColumn() updatedAt: Date;
}
