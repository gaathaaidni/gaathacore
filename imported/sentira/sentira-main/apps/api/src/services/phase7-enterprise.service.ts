import { Injectable } from '@nestjs/common';
import { createHash } from 'crypto';

export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type CameraState = 'ONLINE' | 'CONNECTING' | 'DEGRADED' | 'OFFLINE' | 'AUTH_ERROR' | 'STREAM_ERROR' | 'AI_PROCESSING' | 'DISABLED';

export interface DetectionModelMetadata { model: string; modelVersion: string; device: string; processingTimeMs: number; confidenceThreshold: number; imageSize: number; classes: string[] }
export interface EvidenceIntegrityInput { bytes: Buffer; mediaType: string; durationSeconds?: number; width?: number; height?: number; frameRate?: number; cameraId: string; eventId: string; createdAt?: Date }
export interface EvidenceIntegrityRecord { sha256: string; mediaType: string; fileSizeBytes: number; durationSeconds?: number; resolution?: string; frameRate?: number; cameraId: string; eventId: string; createdAt: string }
export interface AlertPolicy { cooldownSeconds: number; duplicateWindowSeconds: number; notificationLimit: number; suppressionWindowSeconds: number }
export interface AlertDecision { allowed: boolean; groupedKey: string; reason?: string; count: number }

@Injectable()
export class Phase7EnterpriseService {
  private readonly alertWindows = new Map<string, { firstSeenMs: number; lastSeenMs: number; count: number }>();

  createEvidenceIntegrity(input: EvidenceIntegrityInput): EvidenceIntegrityRecord {
    return {
      sha256: createHash('sha256').update(input.bytes).digest('hex'),
      mediaType: input.mediaType,
      fileSizeBytes: input.bytes.byteLength,
      durationSeconds: input.durationSeconds,
      resolution: input.width && input.height ? `${input.width}x${input.height}` : undefined,
      frameRate: input.frameRate,
      cameraId: input.cameraId,
      eventId: input.eventId,
      createdAt: (input.createdAt ?? new Date()).toISOString(),
    };
  }

  classifyCameraHealth(input: { enabled: boolean; connected: boolean; authFailed?: boolean; streamErrors?: number; fps?: number; expectedFps?: number; staleFrameMs?: number; aiProcessing?: boolean }): { state: CameraState; score: number; errors: string[] } {
    if (!input.enabled) return { state: 'DISABLED', score: 0, errors: [] };
    if (input.authFailed) return { state: 'AUTH_ERROR', score: 0, errors: ['authentication_failed'] };
    if (!input.connected) return { state: 'OFFLINE', score: 0, errors: ['not_connected'] };
    const errors: string[] = [];
    let score = 100;
    if ((input.streamErrors ?? 0) > 0) { score -= Math.min(50, (input.streamErrors ?? 0) * 10); errors.push('stream_errors'); }
    if ((input.staleFrameMs ?? 0) > 5000) { score -= 35; errors.push('stale_frame'); }
    if (input.expectedFps && (input.fps ?? 0) < input.expectedFps * 0.5) { score -= 25; errors.push('low_fps'); }
    if (input.aiProcessing) return { state: 'AI_PROCESSING', score: Math.max(0, score), errors };
    return { state: score >= 80 ? 'ONLINE' : 'DEGRADED', score: Math.max(0, score), errors };
  }

  shouldAlert(scope: { organizationId: string; cameraId: string; ruleId: string; trackingKey?: string; severity: Severity }, policy: AlertPolicy, nowMs = Date.now()): AlertDecision {
    const groupedKey = [scope.organizationId, scope.cameraId, scope.ruleId, scope.trackingKey ?? 'frame', scope.severity].join(':');
    const current = this.alertWindows.get(groupedKey);
    if (!current || nowMs - current.lastSeenMs > policy.suppressionWindowSeconds * 1000) {
      this.alertWindows.set(groupedKey, { firstSeenMs: nowMs, lastSeenMs: nowMs, count: 1 });
      return { allowed: true, groupedKey, count: 1 };
    }
    current.lastSeenMs = nowMs;
    current.count += 1;
    if (nowMs - current.firstSeenMs < policy.cooldownSeconds * 1000) return { allowed: false, groupedKey, reason: 'cooldown', count: current.count };
    if (current.count > policy.notificationLimit) return { allowed: false, groupedKey, reason: 'notification_limit', count: current.count };
    return { allowed: true, groupedKey, count: current.count };
  }
}
