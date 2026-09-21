import { EventDeduplicationService } from './event-deduplication.service';
import { RuleStateService } from './rule-state.service';
import { RuleEngineService } from './rule-engine.service';
import { NotificationQueueService } from './notification-queue.service';

describe('Phase 6 production services', () => {
  it('deduplicates repeated detections but allows separate tenants and TTL expiry', async () => {
    const service = new EventDeduplicationService();
    const key = service.buildKey({ organizationId: 'org-a', cameraId: 'cam-a', ruleId: 'rule-a', trackingKey: 'track-1' });
    expect(await service.reserve(key, 1, 1000)).toBe(true);
    expect(await service.reserve(key, 1, 1100)).toBe(false);
    expect(await service.reserve(key.replace('org-a', 'org-b'), 1, 1100)).toBe(true);
    expect(await service.reserve(key, 1, 2101)).toBe(true);
  });

  it('persists temporal state with expiry', async () => {
    const state = new RuleStateService();
    const key = state.key({ organizationId: 'org', cameraId: 'cam', ruleId: 'rule', trackingKey: 'track' });
    await state.touch(key, new Date(1000), 1);
    await state.touch(key, new Date(1500), 1);
    expect((await state.get(key))?.count).toBe(2);
    expect(state.cleanup(3000)).toBe(1);
  });

  it('evaluates persisted advanced zone and duration rules with cooldown', async () => {
    const engine = new RuleEngineService(new EventDeduplicationService(), new RuleStateService());
    const rule: any = { id: 'rule', organizationId: 'org', isActive: true, status: 'active', ruleType: 'advanced', confidenceThreshold: 0.8, duplicateWindowSeconds: 30, cooldownSeconds: 30, definitionJson: { trigger: 'object_detected', conditions: { type: 'duration', objectType: 'person', zoneId: 'zone-a', durationSeconds: 60 } } };
    const frame: any = { organizationId: 'org', cameraId: 'cam', timestamp: new Date(120000).toISOString(), tracks: [{ trackId: 't1', organizationId: 'org', cameraId: 'cam', className: 'person', confidence: 0.95, zoneIds: ['zone-a'], firstSeen: new Date(0).toISOString(), lastSeen: new Date(120000).toISOString(), lastUpdated: new Date(120000).toISOString(), bbox: { x: 1, y: 1, width: 1, height: 1 } }] };
    expect((await engine.evaluateAdvancedRule(rule, frame)).matched).toBe(true);
    expect((await engine.evaluateAdvancedRule(rule, frame)).reason).toBe('duplicate_or_cooldown');
  });

  it('queues notifications asynchronously with idempotency', async () => {
    const sent: string[] = [];
    const queue = new NotificationQueueService({ notify: async (payload: any) => { sent.push(payload.eventId); return {} as any; } } as any);
    queue.enqueue({ organizationId: 'org', eventId: 'event', channel: 'in_app', priority: 'critical', message: 'hello' });
    queue.enqueue({ organizationId: 'org', eventId: 'event', channel: 'in_app', priority: 'critical', message: 'hello' });
    expect(queue.depth()).toBe(1);
    expect(await queue.drain()).toBe(1);
    expect(sent).toEqual(['event']);
  });
});
