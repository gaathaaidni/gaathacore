import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn } from 'typeorm';

@Entity('cctv_connection_tests')
@Index(['organizationId', 'setupSessionId', 'createdAt'])
export class CctvConnectionTest {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ type: 'uuid' }) organizationId: string;
  @Column({ type: 'uuid' }) setupSessionId: string;
  @Column({ type: 'uuid', nullable: true }) cameraId: string;
  @Column({ type: 'varchar', length: 40 }) connectorType: string;
  @Column({ type: 'varchar', length: 20 }) protocol: string;
  @Column({ type: 'varchar', length: 32 }) status: 'VERIFIED_CONNECTED' | 'FAILED';
  @Column({ type: 'varchar', length: 64, nullable: true }) failureCode: string;
  @Column({ type: 'jsonb', default: '{}' }) diagnostics: Record<string, unknown>;
  @Column({ type: 'integer', nullable: true }) durationMs: number;
  @CreateDateColumn() createdAt: Date;
}
