import { Column, CreateDateColumn, Entity, Index, JoinColumn, ManyToOne, PrimaryGeneratedColumn } from 'typeorm';
import { User } from './user.entity';

@Entity('user_sessions')
@Index(['userId', 'revokedAt'])
export class UserSession {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ type: 'uuid' }) userId: string;
  @ManyToOne(() => User, { onDelete: 'CASCADE' }) @JoinColumn({ name: 'userId' }) user: User;
  @Column({ type: 'varchar', length: 255 }) refreshTokenHash: string;
  @Column({ type: 'timestamptz' }) expiresAt: Date;
  @Column({ type: 'timestamptz', nullable: true }) revokedAt: Date;
  @Column({ type: 'varchar', length: 255, nullable: true }) userAgent: string;
  @Column({ type: 'varchar', length: 64, nullable: true }) ipAddress: string;
  @CreateDateColumn() createdAt: Date;
}
