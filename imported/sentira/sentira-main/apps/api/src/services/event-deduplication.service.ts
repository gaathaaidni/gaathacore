import { Injectable, Optional } from '@nestjs/common';
import { RedisStateClient } from './redis-state.client';

@Injectable()
export class EventDeduplicationService {
  private readonly keys = new Map<string, number>();
  constructor(@Optional() private readonly redis?: RedisStateClient) {}

  buildKey(scope: { organizationId: string; cameraId: string; ruleId: string; trackingKey: string }): string {
    return `sentira:event:${scope.organizationId}:${scope.cameraId}:${scope.ruleId}:${scope.trackingKey}`;
  }

  async reserve(key: string, ttlSeconds: number, now = Date.now()): Promise<boolean> {
    if (this.redis) return (await this.redis.command(['SET', key, '1', 'NX', 'EX', String(ttlSeconds)])) === 'OK';
    this.cleanup(now);
    if (this.keys.has(key)) return false;
    this.keys.set(key, now + ttlSeconds * 1000);
    return true;
  }

  cleanup(now = Date.now()): number {
    let removed = 0;
    for (const [key, expiresAt] of this.keys.entries()) {
      if (expiresAt <= now) { this.keys.delete(key); removed += 1; }
    }
    return removed;
  }
}
