export type Operator = '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in' | 'between';
export type Logic = 'AND' | 'OR' | 'NOT';

export interface BBox { x: number; y: number; width: number; height: number }
export interface TrackObject {
  trackId: string;
  cameraId: string;
  organizationId: string;
  siteId?: string;
  className: string;
  confidence: number;
  bbox: BBox;
  firstSeen: string;
  lastSeen: string;
  lastUpdated: string;
  velocity?: { x: number; y: number };
  zoneIds?: string[];
  state?: string;
}
export interface RuleConditionNode {
  type: string;
  field?: string;
  operator?: Operator;
  value?: any;
  objectType?: string;
  zoneId?: string;
  lineId?: string;
  direction?: 'A_TO_B' | 'B_TO_A';
  durationSeconds?: number;
  count?: { objectType?: string; zoneId?: string; operator: Operator; value: number };
  children?: RuleConditionNode[];
  logic?: Logic;
}
export interface RuleSequenceStep { condition: RuleConditionNode; withinSeconds?: number }
export interface Phase5RuleDefinition {
  trigger: string;
  conditions?: RuleConditionNode;
  sequence?: RuleSequenceStep[];
  cooldownSeconds?: number;
}
export interface RuleEvaluationFrame {
  timestamp: string;
  cameraId: string;
  organizationId: string;
  tracks: TrackObject[];
  lineCrossings?: Array<{ trackId: string; lineId: string; direction: 'A_TO_B' | 'B_TO_A'; className: string }>;
}

function compare(actual: any, operator: Operator = '==', expected: any): boolean {
  switch (operator) {
    case '==': return actual === expected;
    case '!=': return actual !== expected;
    case '>': return Number(actual) > Number(expected);
    case '>=': return Number(actual) >= Number(expected);
    case '<': return Number(actual) < Number(expected);
    case '<=': return Number(actual) <= Number(expected);
    case 'in': return Array.isArray(expected) && expected.includes(actual);
    case 'between': return Array.isArray(expected) && Number(actual) >= expected[0] && Number(actual) <= expected[1];
  }
}

export class Phase5RuleEngine {
  private sequenceState = new Map<string, { index: number; startedAt: number }>();

  evaluate(definition: Phase5RuleDefinition, frame: RuleEvaluationFrame): boolean {
    if (definition.sequence?.length) return this.evaluateSequence(definition, frame);
    return definition.conditions ? this.evaluateNode(definition.conditions, frame) : this.evaluateTrigger(definition.trigger, frame);
  }

  evaluateNode(node: RuleConditionNode, frame: RuleEvaluationFrame): boolean {
    if (node.children?.length) {
      const values = node.children.map((child) => this.evaluateNode(child, frame));
      if (node.logic === 'OR') return values.some(Boolean);
      if (node.logic === 'NOT') return !values[0];
      return values.every(Boolean);
    }

    if (node.type === 'object_detected' || node.type === 'object_present') {
      return frame.tracks.some((track) => this.matchesTrack(track, node));
    }
    if (node.type === 'object_absent') {
      return !frame.tracks.some((track) => this.matchesTrack(track, node));
    }
    if (node.type === 'zone_entry' || node.type === 'zone_exit') {
      return frame.tracks.some((track) => this.matchesTrack(track, node) && (!node.zoneId || track.zoneIds?.includes(node.zoneId)));
    }
    if (node.type === 'duration') {
      return frame.tracks.some((track) => this.matchesTrack(track, node) && (Date.parse(track.lastSeen) - Date.parse(track.firstSeen)) / 1000 >= (node.durationSeconds ?? 0));
    }
    if (node.type === 'confidence') {
      return frame.tracks.some((track) => compare(track.confidence, node.operator, node.value));
    }
    if (node.type === 'count' && node.count) {
      const count = frame.tracks.filter((track) => (!node.count?.objectType || track.className === node.count.objectType) && (!node.count?.zoneId || track.zoneIds?.includes(node.count.zoneId))).length;
      return compare(count, node.count.operator, node.count.value);
    }
    if (node.type === 'line_crossing') {
      return (frame.lineCrossings ?? []).some((crossing) => (!node.objectType || crossing.className === node.objectType) && (!node.lineId || crossing.lineId === node.lineId) && (!node.direction || crossing.direction === node.direction));
    }
    if (node.field) {
      return frame.tracks.some((track) => compare((track as any)[node.field!], node.operator, node.value));
    }
    return false;
  }

  private evaluateTrigger(trigger: string, frame: RuleEvaluationFrame): boolean {
    return trigger === 'object_detected' ? frame.tracks.length > 0 : false;
  }

  private evaluateSequence(definition: Phase5RuleDefinition, frame: RuleEvaluationFrame): boolean {
    const key = `${frame.organizationId}:${frame.cameraId}:${definition.trigger}`;
    const state = this.sequenceState.get(key) ?? { index: 0, startedAt: Date.parse(frame.timestamp) };
    const step = definition.sequence![state.index];
    if (!step) return false;
    if (step.withinSeconds && (Date.parse(frame.timestamp) - state.startedAt) / 1000 > step.withinSeconds) {
      this.sequenceState.set(key, { index: 0, startedAt: Date.parse(frame.timestamp) });
      return false;
    }
    if (this.evaluateNode(step.condition, frame)) {
      const next = state.index + 1;
      if (next >= definition.sequence!.length) {
        this.sequenceState.delete(key);
        return true;
      }
      this.sequenceState.set(key, { index: next, startedAt: state.startedAt });
    }
    return false;
  }

  private matchesTrack(track: TrackObject, node: RuleConditionNode): boolean {
    return (!node.objectType || track.className === node.objectType) && (!node.zoneId || track.zoneIds?.includes(node.zoneId));
  }
}
