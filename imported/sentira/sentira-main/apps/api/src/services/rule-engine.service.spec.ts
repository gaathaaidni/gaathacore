import { Test, TestingModule } from '@nestjs/testing';
import { RuleEngineService } from './rule-engine.service';
import { Rule } from '../entities/rule.entity';
import { RuleEvaluationContext } from '../common/types';

describe('RuleEngineService', () => {
  let service: RuleEngineService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [RuleEngineService],
    }).compile();

    service = module.get<RuleEngineService>(RuleEngineService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should return false for inactive rules', () => {
    const rule = {
      isActive: false,
      confidenceThreshold: 0.7,
    } as Rule;

    const context: RuleEvaluationContext = {
      cameraId: 'test',
      organizationId: 'test',
      detections: [
        {
          objectType: 'person',
          confidence: 0.95,
          bbox: { x1: 0, y1: 0, x2: 100, y2: 100 },
          trackId: '1',
          timestamp: new Date(),
        },
      ],
      timestamp: new Date(),
    };

    expect(service.evaluateRule(rule, context)).toBe(false);
  });

  it('should return false when confidence is below threshold', () => {
    const rule = {
      isActive: true,
      confidenceThreshold: 0.9,
    } as Rule;

    const context: RuleEvaluationContext = {
      cameraId: 'test',
      organizationId: 'test',
      detections: [
        {
          objectType: 'person',
          confidence: 0.5,
          bbox: { x1: 0, y1: 0, x2: 100, y2: 100 },
          trackId: '1',
          timestamp: new Date(),
        },
      ],
      timestamp: new Date(),
    };

    expect(service.evaluateRule(rule, context)).toBe(false);
  });

  it('should evaluate demo rules for known types', () => {
    const rule = {
      isActive: true,
      ruleType: 'table_unattended',
    } as Rule;

    const result = service.evaluateDemoRules(rule);
    expect(typeof result).toBe('boolean');
  });
});
