import { Column, CreateDateColumn, Entity, Index, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { Organization } from './organization.entity';
import { JoinColumn, ManyToOne } from 'typeorm';

@Entity('connectors')
@Index(['organizationId', 'status'])
export class Connector {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'varchar', length: 32, default: 'pending' })
  status: 'pending' | 'online' | 'offline' | 'disabled';

  @Column({ type: 'text', nullable: true })
  registrationTokenHash: string;

  @Column({ type: 'timestamp', nullable: true })
  lastHeartbeatAt: Date;

  @Column({ type: 'varchar', length: 64, nullable: true })
  version: string;

  @Column({ type: 'jsonb', nullable: true })
  capabilities: Record<string, unknown>;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
