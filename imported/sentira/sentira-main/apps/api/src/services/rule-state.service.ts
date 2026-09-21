import { Injectable, Optional } from '@nestjs/common';
import { RedisStateClient } from './redis-state.client';

export interface RuleStateRecord { firstSeenAt: string; lastSeenAt: string; count: number; sequenceIndex?: number; expiresAt: number }

@Injectable()
export class RuleStateService {
  private readonly state = new Map<string, RuleStateRecord>();
  constructor(@Optional() private readonly redis?: RedisStateClient) {}

  key(scope: { organizationId: string; cameraId: string; ruleId: string; trackingKey: string }): string {
    return `sentira:rule-state:${scope.organizationId}:${scope.cameraId}:${scope.ruleId}:${scope.trackingKey}`;
  }

  async touch(key: string, now: Date, ttlSeconds: number): Promise<RuleStateRecord> {
    const existing = await this.get(key);
    const record: RuleStateRecord = existing ?? { firstSeenAt: now.toISOString(), lastSeenAt: now.toISOString(), count: 0, expiresAt: 0 };
    record.lastSeenAt = now.toISOString();
    record.count += 1;
    record.expiresAt = now.getTime() + ttlSeconds * 1000;
    if (this.redis) await this.redis.command(['SET', key, JSON.stringify(record), 'EX', String(ttlSeconds)]); else this.state.set(key, record);
    return record;
  }

  async get(key: string): Promise<RuleStateRecord | undefined> {
    if (this.redis) { const value = await this.redis.command(['GET', key]); return value ? JSON.parse(value) as RuleStateRecord : undefined; }
    // The in-memory implementation exists only for isolated unit construction;
    // expiry is deterministic through cleanup(now). Runtime uses Redis TTL.
    return this.state.get(key);
  }

  async setSequence(key: string, index: number, now: Date, ttlSeconds: number): Promise<void> {
    const current = (await this.get(key)) ?? { firstSeenAt: now.toISOString(), lastSeenAt: now.toISOString(), count: 0, expiresAt: 0 };
    current.sequenceIndex = index;
    current.lastSeenAt = now.toISOString();
    current.expiresAt = now.getTime() + ttlSeconds * 1000;
    if (this.redis) await this.redis.command(['SET', key, JSON.stringify(current), 'EX', String(ttlSeconds)]); else this.state.set(key, current);
  }

  async delete(key: string): Promise<void> { if (this.redis) await this.redis.command(['DEL', key]); else this.state.delete(key); }

  cleanup(nowMs: number): number {
    let removed = 0;
    for (const [key, value] of this.state.entries()) {
      if (value.expiresAt <= nowMs) { this.state.delete(key); removed += 1; }
    }
    return removed;
  }
}
