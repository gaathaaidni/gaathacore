import { Phase5RuleEngine, RuleEvaluationFrame } from './phase5-rule-engine';

const frame: RuleEvaluationFrame = {
  timestamp: '2026-08-21T00:00:30.000Z', cameraId: 'cam1', organizationId: 'org1',
  tracks: [{ trackId: 't1', cameraId: 'cam1', organizationId: 'org1', siteId: 'site1', className: 'person', confidence: .91, bbox: { x:0,y:0,width:.2,height:.2 }, firstSeen: '2026-08-21T00:00:00.000Z', lastSeen: '2026-08-21T00:00:30.000Z', lastUpdated: '2026-08-21T00:00:30.000Z', zoneIds: ['kitchen'], state: 'confirmed' }],
  lineCrossings: [{ trackId: 't1', lineId: 'entrance', direction: 'A_TO_B', className: 'person' }],
};

describe('Phase5RuleEngine', () => {
  it('evaluates compound duration zone rules', () => {
    const engine = new Phase5RuleEngine();
    expect(engine.evaluate({ trigger: 'object_detected', conditions: { type: 'compound', logic: 'AND', children: [ { type: 'object_present', objectType: 'person', zoneId: 'kitchen' }, { type: 'duration', objectType: 'person', durationSeconds: 30 } ] } }, frame)).toBe(true);
  });
  it('evaluates count and line crossing rules', () => {
    const engine = new Phase5RuleEngine();
    expect(engine.evaluate({ trigger: 'count', conditions: { type: 'count', count: { objectType: 'person', zoneId: 'kitchen', operator: '>=', value: 1 } } }, frame)).toBe(true);
    expect(engine.evaluate({ trigger: 'line_crossing', conditions: { type: 'line_crossing', objectType: 'person', lineId: 'entrance', direction: 'A_TO_B' } }, frame)).toBe(true);
  });
  it('evaluates sequence rules within window', () => {
    const engine = new Phase5RuleEngine();
    const rule = { trigger: 'sequence-demo', sequence: [ { condition: { type: 'zone_entry', objectType: 'person', zoneId: 'kitchen' } }, { condition: { type: 'line_crossing', objectType: 'person', lineId: 'entrance', direction: 'A_TO_B' as const }, withinSeconds: 60 } ] };
    expect(engine.evaluate(rule, frame)).toBe(false);
    expect(engine.evaluate(rule, { ...frame, timestamp: '2026-08-21T00:00:45.000Z' })).toBe(true);
  });
});
