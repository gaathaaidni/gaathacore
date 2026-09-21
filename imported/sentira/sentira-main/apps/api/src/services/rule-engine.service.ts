import { Injectable, Optional } from '@nestjs/common';
import { Rule } from '../entities/rule.entity';
import { RuleEvaluationContext } from '../common/types';
import { EventDeduplicationService } from './event-deduplication.service';
import { RuleStateService } from './rule-state.service';
import { Phase5RuleDefinition, Phase5RuleEngine, RuleEvaluationFrame, TrackObject } from './phase5-rule-engine';

export interface AdvancedRuleEvaluationResult { matched: boolean; trackingKey: string; dedupKey?: string; reason?: string }

@Injectable()
export class RuleEngineService {
  private readonly evaluator = new Phase5RuleEngine();
  constructor(@Optional() private readonly dedup: EventDeduplicationService = new EventDeduplicationService(), @Optional() private readonly state: RuleStateService = new RuleStateService()) {}

  async evaluateAdvancedRule(rule: Rule, frame: RuleEvaluationFrame): Promise<AdvancedRuleEvaluationResult> {
    if (!rule.isActive || rule.status !== 'active') return { matched: false, trackingKey: 'inactive', reason: 'inactive' };
    if (!this.isInSchedule(rule.scheduleJson, new Date(frame.timestamp))) return { matched: false, trackingKey: 'schedule', reason: 'outside_schedule' };
    const tracks = frame.tracks.filter((track) => track.confidence >= Number(rule.confidenceThreshold ?? 0));
    const scopedFrame = { ...frame, tracks };
    const definition = (rule.definitionJson ?? { trigger: rule.ruleType }) as unknown as Phase5RuleDefinition;
    const matched = this.evaluator.evaluate(definition, scopedFrame);
    if (!matched) return { matched: false, trackingKey: 'conditions', reason: 'conditions_not_met' };
    const trackingKey = this.trackingKey(scopedFrame.tracks);
    const stateKey = this.state.key({ organizationId: rule.organizationId, cameraId: frame.cameraId, ruleId: rule.id, trackingKey });
    await this.state.touch(stateKey, new Date(frame.timestamp), Math.max(rule.cooldownSeconds ?? 60, 60));
    const dedupKey = this.dedup.buildKey({ organizationId: rule.organizationId, cameraId: frame.cameraId, ruleId: rule.id, trackingKey });
    const reserved = await this.dedup.reserve(dedupKey, Math.max(rule.duplicateWindowSeconds ?? rule.cooldownSeconds ?? 10, 1));
    return reserved ? { matched: true, trackingKey, dedupKey } : { matched: false, trackingKey, dedupKey, reason: 'duplicate_or_cooldown' };
  }

  evaluateRule(rule: Rule, context: RuleEvaluationContext): boolean {
    if (!rule.isActive) return false;
    const maxConfidence = Math.max(...context.detections.map((d) => d.confidence || 0), 0);
    return maxConfidence >= Number(rule.confidenceThreshold) && this.isInSchedule(rule.scheduleJson, new Date());
  }

  evaluateDemoRules(rule: Rule): boolean { return rule.isActive && Math.random() < 0.7; }

  private trackingKey(tracks: TrackObject[]): string {
    const stable = tracks.map((track) => track.trackId || `${track.className}:${track.zoneIds?.join(',') ?? 'no-zone'}`).sort().join('|');
    return stable || 'frame';
  }

  private isInSchedule(scheduleJson: Record<string, unknown>, now: Date): boolean {
    if (!scheduleJson) return true;
    const schedule = scheduleJson as { days?: string[]; start?: string; end?: string };
    const dayName = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][now.getDay()];
    if (schedule.days?.length && !schedule.days.includes(dayName)) return false;
    if (schedule.start && schedule.end) {
      const minutes = now.getHours() * 60 + now.getMinutes();
      const [sh, sm] = schedule.start.split(':').map(Number);
      const [eh, em] = schedule.end.split(':').map(Number);
      return minutes >= sh * 60 + (sm || 0) && minutes <= eh * 60 + (em || 0);
    }
    return true;
  }
}
