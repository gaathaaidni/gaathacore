import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { Connector } from './connector.entity';
import { Organization } from './organization.entity';

@Entity('discovered_cameras')
@Index(['organizationId', 'connectorId', 'discoveryStatus'])
export class DiscoveredCamera {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ type: 'uuid' }) organizationId: string;
  @ManyToOne(() => Organization, { onDelete: 'CASCADE' }) @JoinColumn({ name: 'organizationId' }) organization: Organization;
  @Column({ type: 'uuid' }) connectorId: string;
  @ManyToOne(() => Connector, { onDelete: 'CASCADE' }) @JoinColumn({ name: 'connectorId' }) connector: Connector;
  @Column({ type: 'varchar', length: 255 }) name: string;
  @Column({ type: 'varchar', length: 255, nullable: true }) localAddress: string;
  @Column({ type: 'varchar', length: 100, nullable: true }) manufacturer: string;
  @Column({ type: 'varchar', length: 100, nullable: true }) model: string;
  @Column({ type: 'varchar', length: 50, nullable: true }) protocol: string;
  @Column({ type: 'jsonb', nullable: true }) capabilities: Record<string, unknown>;
  @Column({ type: 'varchar', length: 32, default: 'ready' }) discoveryStatus: 'ready' | 'claimed' | 'unsupported';
  @Column({ type: 'timestamp' }) discoveredAt: Date;
  @UpdateDateColumn() updatedAt: Date;
}
