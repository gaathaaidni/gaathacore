import {
  Column,
  CreateDateColumn,
  Entity,
  ManyToOne,
  PrimaryGeneratedColumn,
  Index,
  JoinColumn,
} from 'typeorm';

import { Rule } from './rule.entity';

@Entity('rule_actions')
@Index(['ruleId'])
export class RuleAction {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  ruleId: string;

  @ManyToOne(() => Rule, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'ruleId' })
  rule: Rule;

  @Column({ type: 'varchar', length: 100 })
  actionType: string;

  @Column({ type: 'jsonb', nullable: true })
  configJson: Record<string, any>;

  @CreateDateColumn()
  createdAt: Date;
}
