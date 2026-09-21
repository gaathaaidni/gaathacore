import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';
import { CctvManufacturer } from './cctv-manufacturer.entity';

export type CctvDeviceType = 'WIFI_CAMERA' | 'IP_CAMERA' | 'ANALOG_CAMERA' | 'DVR' | 'NVR' | 'XVR' | 'CAMERA_SYSTEM' | 'OTHER';

@Entity('cctv_models')
@Index(['manufacturerId', 'slug'], { unique: true })
export class CctvModel {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  manufacturerId: string;

  @ManyToOne(() => CctvManufacturer, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'manufacturerId' })
  manufacturer: CctvManufacturer;

  @Column({ type: 'varchar', length: 160 })
  modelNumber: string;

  @Column({ type: 'varchar', length: 180 })
  name: string;

  @Column({ type: 'varchar', length: 180 })
  slug: string;

  @Column({ type: 'varchar', length: 40 })
  deviceType: CctvDeviceType;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ type: 'jsonb', default: '[]' })
  supportedProtocols: Array<{ protocol: string; status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNKNOWN' | 'NOT_SUPPORTED' | 'REQUIRES_ASSISTANCE'; verified: boolean; notes?: string }>;

  @Column({ type: 'jsonb', default: '[]' })
  discoveryMethods: string[];

  @Column({ type: 'boolean', default: true })
  active: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
