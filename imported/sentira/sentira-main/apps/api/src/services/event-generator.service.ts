import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Event } from '../entities/event.entity';
import { EventPayload } from '../common/types';
import { Rule } from '../entities/rule.entity';
import { DetectionEnvelope } from './detection-envelope';

@Injectable()
export class EventGeneratorService {
  constructor(
    @InjectRepository(Event)
    private eventsRepository: Repository<Event>,
  ) {}

  async createDemoEvent(payload: EventPayload): Promise<Event> {
    const event = await this.eventsRepository.save({
      organizationId: payload.organizationId,
      siteId: payload.siteId,
      cameraId: payload.cameraId,
      ruleId: payload.ruleId,
      zoneId: payload.zoneId,
      eventType: payload.eventType,
      severity: payload.severity,
      confidence: payload.confidence,
      description: payload.description,
      status: 'new',
      snapshotUrl: `/demo/snapshot/${payload.cameraId}/${Date.now()}.jpg`,
      videoClipUrl: `/demo/video/${payload.cameraId}/${Date.now()}.mp4`,
    });

    return event;
  }

  async createEventFromDetections(
    organizationId: string,
    siteId: string,
    cameraId: string,
    ruleId: string,
    eventType: string,
    severity: 'low' | 'medium' | 'high' | 'critical' = 'medium',
    confidence: number = 0.85,
  ): Promise<Event> {
    return this.createDemoEvent({
      organizationId,
      siteId,
      cameraId,
      ruleId,
      eventType,
      severity,
      confidence,
      description: `Demo event: ${eventType} detected on camera`,
      detections: [],
    });
  }

  async createDetectionEvent(input: { detection: DetectionEnvelope; rule: Rule; trackingKey: string }): Promise<Event> {
    const { detection, rule, trackingKey } = input;
    const confidence = Math.max(...detection.objects.map((object) => object.confidence), 0);
    return this.eventsRepository.save({
      organizationId: detection.organizationId, siteId: detection.siteId, cameraId: detection.cameraId,
      ruleId: rule.id, eventType: rule.ruleType, severity: rule.severity, confidence,
      description: `${rule.name}: ${detection.objects.map((object) => object.class_name).join(', ') || 'detection'} detected`,
      status: 'new', firstDetectedAt: new Date(detection.timestamp), lastDetectedAt: new Date(detection.timestamp),
      trackId: trackingKey, model: detection.model, modelVersion: detection.modelVersion,
      ruleVersion: rule.version, evidenceStatus: detection.jpegBase64 ? 'processing' : 'pending',
      correlationId: detection.correlationId ?? detection.frameId,
    });
  }
}
