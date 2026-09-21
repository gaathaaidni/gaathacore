import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Rule } from '../../entities/rule.entity';
import { RuleCondition } from '../../entities/rule-condition.entity';
import { RuleAction } from '../../entities/rule-action.entity';

@Injectable()
export class RulesService {
  constructor(
    @InjectRepository(Rule)
    private rulesRepository: Repository<Rule>,
    @InjectRepository(RuleCondition)
    private conditionsRepository: Repository<RuleCondition>,
    @InjectRepository(RuleAction)
    private actionsRepository: Repository<RuleAction>,
  ) {}

  async create(organizationId: string, ruleData: Partial<Rule>): Promise<Rule> {
    return this.rulesRepository.save({
      ...ruleData,
      organizationId,
    });
  }

  async findById(id: string, organizationId: string): Promise<Rule | null> {
    return this.rulesRepository.findOne({
      where: { id, organizationId },
      relations: ['site', 'camera', 'conditions', 'actions'],
    });
  }

  async findByOrganization(organizationId: string): Promise<Rule[]> {
    return this.rulesRepository.find({
      where: { organizationId, isActive: true },
      relations: ['conditions', 'actions', 'camera'],
    });
  }

  async addCondition(ruleId: string, condition: Partial<RuleCondition>): Promise<RuleCondition> {
    return this.conditionsRepository.save({
      ...condition,
      ruleId,
    });
  }

  async addAction(ruleId: string, action: Partial<RuleAction>): Promise<RuleAction> {
    return this.actionsRepository.save({
      ...action,
      ruleId,
    });
  }
}
