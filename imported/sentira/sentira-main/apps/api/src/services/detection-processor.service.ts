import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Camera, Rule } from '../entities';
import { RuleEngineService } from './rule-engine.service';
import { EventGeneratorService } from './event-generator.service';
import { EvidenceService } from './evidence.service';
import { EventsGateway } from '../events.gateway';
import { DetectionEnvelope } from './detection-envelope';

@Injectable()
export class DetectionProcessorService {
  private readonly logger = new Logger(DetectionProcessorService.name);
  constructor(@InjectRepository(Camera) private readonly cameras: Repository<Camera>, @InjectRepository(Rule) private readonly rules: Repository<Rule>, private readonly ruleEngine: RuleEngineService, private readonly events: EventGeneratorService, private readonly evidence: EvidenceService, private readonly gateway: EventsGateway) {}

  async process(detection: DetectionEnvelope): Promise<void> {
    const camera = await this.cameras.findOneBy({ id: detection.cameraId, organizationId: detection.organizationId, siteId: detection.siteId });
    if (!camera) throw new Error('Detection camera is not in the declared tenant/site');
    const rules = await this.rules.find({ where: { organizationId: detection.organizationId, isActive: true, status: 'active' } });
    for (const rule of rules.filter((candidate) => !candidate.cameraId || candidate.cameraId === camera.id)) {
      const detectedAt = new Date(detection.timestamp).toISOString();
      const result = await this.ruleEngine.evaluateAdvancedRule(rule, { organizationId: detection.organizationId, cameraId: camera.id, timestamp: detection.timestamp, tracks: detection.objects.map((object) => ({ className: object.class_name, confidence: object.confidence, bbox: { x: object.bbox[0], y: object.bbox[1], width: object.bbox[2], height: object.bbox[3] }, trackId: object.trackId ?? detection.frameId, zoneIds: object.zoneIds, cameraId: camera.id, organizationId: detection.organizationId, siteId: detection.siteId, firstSeen: detectedAt, lastSeen: detectedAt, lastUpdated: detectedAt })) });
      if (!result.matched) continue;
      const event = await this.events.createDetectionEvent({ detection, rule, trackingKey: result.trackingKey });
      this.gateway.broadcastEventCreated(event);
      if (detection.jpegBase64) void this.evidence.attachSnapshot(event, detection.jpegBase64, detection.correlationId).catch((error: Error) => this.logger.error(JSON.stringify({ message: 'snapshot evidence failed', eventId: event.id, correlationId: detection.correlationId, error: error.message })));
      this.logger.log(JSON.stringify({ message: 'detection created event', eventId: event.id, ruleId: rule.id, cameraId: camera.id, correlationId: detection.correlationId ?? detection.frameId }));
    }
  }
}
