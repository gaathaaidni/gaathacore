import { BadRequestException } from '@nestjs/common';

export interface DetectionObject {
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
  trackId?: string;
  zoneIds?: string[];
}

export interface DetectionEnvelope {
  organizationId: string; siteId: string; cameraId: string; timestamp: string; frameId: string;
  correlationId?: string; jpegBase64?: string; model: string; modelVersion: string;
  processingTimeMs: number; objects: DetectionObject[];
}

export function parseDetectionEnvelope(value: unknown): DetectionEnvelope {
  if (!value || typeof value !== 'object') throw new BadRequestException('Detection envelope must be an object');
  const input = value as Record<string, unknown>;
  for (const field of ['organizationId', 'siteId', 'cameraId', 'timestamp', 'frameId', 'model', 'modelVersion']) {
    if (typeof input[field] !== 'string' || !input[field]) throw new BadRequestException(`Detection ${field} is required`);
  }
  if (!Number.isFinite(input.processingTimeMs) || Number(input.processingTimeMs) < 0) throw new BadRequestException('Detection processingTimeMs is invalid');
  if (!Array.isArray(input.objects)) throw new BadRequestException('Detection objects must be an array');
  const objects = input.objects.map((item) => {
    const object = item as Record<string, unknown>;
    if (!object || typeof object.class_name !== 'string' || !Number.isFinite(object.confidence) || !Array.isArray(object.bbox) || object.bbox.length !== 4 || !object.bbox.every(Number.isFinite)) throw new BadRequestException('Detection object is invalid');
    if (Number(object.confidence) < 0 || Number(object.confidence) > 1) throw new BadRequestException('Detection confidence is invalid');
    return { class_name: object.class_name, confidence: Number(object.confidence), bbox: object.bbox as [number, number, number, number], trackId: typeof object.trackId === 'string' ? object.trackId : undefined, zoneIds: Array.isArray(object.zoneIds) ? object.zoneIds.filter((id): id is string => typeof id === 'string') : undefined };
  });
  if (Number.isNaN(new Date(input.timestamp as string).getTime())) throw new BadRequestException('Detection timestamp is invalid');
  return { organizationId: input.organizationId as string, siteId: input.siteId as string, cameraId: input.cameraId as string, timestamp: input.timestamp as string, frameId: input.frameId as string, correlationId: typeof input.correlationId === 'string' ? input.correlationId : undefined, jpegBase64: typeof input.jpegBase64 === 'string' ? input.jpegBase64 : undefined, model: input.model as string, modelVersion: input.modelVersion as string, processingTimeMs: Number(input.processingTimeMs), objects };
}
