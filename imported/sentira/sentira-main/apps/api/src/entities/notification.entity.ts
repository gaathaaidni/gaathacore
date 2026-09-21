import {
  Column,
  CreateDateColumn,
  Entity,
  ManyToOne,
  PrimaryGeneratedColumn,
  Index,
  JoinColumn,
} from 'typeorm';
import { Organization } from './organization.entity';
import { Event } from './event.entity';
import { User } from './user.entity';

@Entity('notifications')
@Index(['organizationId', 'createdAt'])
@Index(['status'])
export class Notification {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  organizationId: string;

  @ManyToOne(() => Organization, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'organizationId' })
  organization: Organization;

  @Column({ type: 'uuid', nullable: true })
  eventId: string;

  @ManyToOne(() => Event, { onDelete: 'CASCADE', nullable: true })
  @JoinColumn({ name: 'eventId' })
  event: Event;

  @Column({ type: 'uuid', nullable: true })
  userId: string;

  @ManyToOne(() => User, { onDelete: 'SET NULL', nullable: true })
  @JoinColumn({ name: 'userId' })
  user: User;

  @Column({ type: 'varchar', length: 100 })
  channel: 'in_app' | 'email' | 'push' | 'webhook';

  @Column({ type: 'varchar', length: 50 })
  priority: 'low' | 'medium' | 'high' | 'critical';

  @Column({ type: 'varchar', length: 50, default: 'pending' })
  status: 'pending' | 'sent' | 'failed' | 'read';

  @Column({ type: 'timestamp', nullable: true })
  sentAt: Date;

  @Column({ type: 'jsonb', nullable: true })
  payload: Record<string, any>;

  @CreateDateColumn()
  createdAt: Date;
}
