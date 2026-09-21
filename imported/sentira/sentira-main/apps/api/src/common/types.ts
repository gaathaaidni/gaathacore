export interface Detection {
  objectType: string;
  confidence: number;
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  trackId: string;
  timestamp: Date;
  zoneId?: string;
}

export interface EventPayload {
  cameraId: string;
  organizationId: string;
  siteId: string;
  eventType: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  detections: Detection[];
  ruleId?: string;
  zoneId?: string;
}

export interface RuleEvaluationContext {
  cameraId: string;
  organizationId: string;
  detections: Detection[];
  timestamp: Date;
  duration?: number;
}
