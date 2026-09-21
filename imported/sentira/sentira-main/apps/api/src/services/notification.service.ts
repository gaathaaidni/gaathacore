import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Event } from '../entities/event.entity';
import { Notification } from '../entities/notification.entity';

export interface NotificationPayload {
  organizationId: string;
  eventId: string;
  userId?: string;
  channel: 'in_app' | 'email' | 'push' | 'webhook';
  priority: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  payload?: Record<string, any>;
}

@Injectable()
export class NotificationService {
  constructor(
    @InjectRepository(Notification)
    private notificationsRepository: Repository<Notification>,
  ) {}

  async notify(payload: NotificationPayload): Promise<Notification> {
    const notification = await this.notificationsRepository.save({
      organizationId: payload.organizationId,
      eventId: payload.eventId,
      userId: payload.userId,
      channel: payload.channel,
      priority: payload.priority,
      payload: {
        message: payload.message,
        ...payload.payload,
      },
      status: 'sent',
      sentAt: new Date(),
    });

    // In production, would actually send via email, push service, webhook, etc.
    console.log(`[${payload.channel.toUpperCase()}] Notification sent:`, notification);

    return notification;
  }

  async notifyEvent(event: Event, message: string): Promise<Notification> {
    // Determine priority based on severity
    const priorityMap = {
      low: 'low',
      medium: 'medium',
      high: 'high',
      critical: 'critical',
    };

    return this.notify({
      organizationId: event.organizationId,
      eventId: event.id,
      channel: 'in_app',
      priority: priorityMap[event.severity] as any,
      message,
      payload: {
        eventType: event.eventType,
        camera: event.camera?.name,
        description: event.description,
      },
    });
  }
}
