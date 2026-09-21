import { Injectable, Logger } from '@nestjs/common';
import { NotificationService, NotificationPayload } from './notification.service';

interface QueuedNotification extends NotificationPayload { idempotencyKey: string; attempts: number; nextAttemptAt: number }

@Injectable()
export class NotificationQueueService {
  private readonly logger = new Logger(NotificationQueueService.name);
  private readonly queue: QueuedNotification[] = [];
  private readonly completed = new Set<string>();
  constructor(private readonly notificationService: NotificationService) {}

  enqueue(payload: NotificationPayload & { idempotencyKey?: string }): string {
    const key = payload.idempotencyKey ?? `notification:${payload.organizationId}:${payload.eventId}:${payload.channel}:${payload.userId ?? 'org'}`;
    if (this.completed.has(key) || this.queue.some((item) => item.idempotencyKey === key)) return key;
    this.queue.push({ ...payload, idempotencyKey: key, attempts: 0, nextAttemptAt: Date.now() });
    this.queue.sort((a, b) => this.priority(b.priority) - this.priority(a.priority));
    return key;
  }

  async drain(now = Date.now()): Promise<number> {
    let processed = 0;
    for (const item of [...this.queue]) {
      if (item.nextAttemptAt > now) continue;
      try {
        item.attempts += 1;
        await this.notificationService.notify(item);
        this.completed.add(item.idempotencyKey);
        this.queue.splice(this.queue.indexOf(item), 1);
        processed += 1;
      } catch (error) {
        item.nextAttemptAt = now + Math.min(60000, 2 ** item.attempts * 1000);
        this.logger.error(`Notification delivery failed`, { organizationId: item.organizationId, eventId: item.eventId, channel: item.channel, attempts: item.attempts, error: error instanceof Error ? error.message : String(error) });
        if (item.attempts >= 5) this.queue.splice(this.queue.indexOf(item), 1);
      }
    }
    return processed;
  }

  depth(): number { return this.queue.length; }
  private priority(value: string): number { return { low: 1, medium: 2, high: 3, critical: 4 }[value] ?? 1; }
}
