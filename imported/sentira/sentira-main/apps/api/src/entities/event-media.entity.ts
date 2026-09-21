import {
  Column,
  CreateDateColumn,
  Entity,
  ManyToOne,
  PrimaryGeneratedColumn,
  Index,
  JoinColumn,
} from 'typeorm';

import { Event } from './event.entity';

@Entity('event_media')
@Index(['eventId'])
export class EventMedia {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  eventId: string;

  @ManyToOne(() => Event, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'eventId' })
  event: Event;

  @Column({ type: 'varchar', length: 100 })
  mediaType: 'snapshot' | 'video_clip' | 'detection_json';

  @Column({ type: 'uuid' })
  organizationId: string;

  @Column({ type: 'uuid' })
  cameraId: string;

  @Column({ type: 'varchar', length: 500 })
  storageKey: string;

  @Column({ type: 'varchar', length: 500, nullable: true })
  storageUrl: string;

  @Column({ type: 'varchar', length: 64, nullable: true })
  sha256: string;

  @Column({ type: 'integer', nullable: true })
  byteSize: number;

  @Column({ type: 'varchar', length: 128, nullable: true })
  contentType: string;

  @Column({ type: 'integer', nullable: true })
  width: number;

  @Column({ type: 'integer', nullable: true })
  height: number;

  @Column({ type: 'integer', nullable: true })
  durationSeconds: number;

  @Column({ type: 'timestamptz', nullable: true })
  capturedAt: Date;

  @Column({ type: 'timestamptz', nullable: true })
  expiresAt: Date;

  @Column({ type: 'jsonb', nullable: true })
  metadataJson: Record<string, unknown>;

  @CreateDateColumn()
  createdAt: Date;
}
