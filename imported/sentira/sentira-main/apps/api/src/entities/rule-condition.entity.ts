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

@Entity('rule_conditions')
@Index(['ruleId'])
export class RuleCondition {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  ruleId: string;

  @ManyToOne(() => Rule, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'ruleId' })
  rule: Rule;

  @Column({ type: 'varchar', length: 100 })
  conditionType: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  fieldName: string;

  @Column({ type: 'varchar', length: 100, nullable: true })
  operator: string;

  @Column({ type: 'jsonb', nullable: true })
  valueJson: Record<string, any>;

  @Column({ type: 'integer', default: 0 })
  sequenceOrder: number;

  @CreateDateColumn()
  createdAt: Date;
}
