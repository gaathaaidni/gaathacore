import { Injectable } from '@nestjs/common';

export interface ActionPayload { eventId: string; organizationId: string; cameraId?: string; eventType?: string; severity?: string; timestamp?: string }
export interface RuleActionDefinition { type: string; target?: string; cooldownSeconds?: number; metadata?: Record<string, unknown> }
export interface ActionResult { status: 'queued' | 'sent' | 'skipped'; actionType: string; organizationId: string; eventId: string }

@Injectable()
export class ActionExecutorService {
  async execute(action: RuleActionDefinition, payload: ActionPayload): Promise<ActionResult> {
    return { status: action.type === 'webhook' ? 'sent' : 'queued', actionType: action.type, organizationId: payload.organizationId, eventId: payload.eventId };
  }
}
