import { Injectable } from '@nestjs/common';
import { CctvConnector, ConnectionVerificationResult } from './cctv-connector';

@Injectable()
export class OnvifConnector implements CctvConnector {
  getId() { return 'onvif-edge'; }
  getName() { return 'ONVIF via Sentira Edge Connector'; }
  supports(deviceType: string) { return ['WIFI_CAMERA', 'IP_CAMERA', 'DVR', 'NVR', 'CAMERA_SYSTEM', 'OTHER'].includes(deviceType); }
  supportsProtocol(protocol: string) { return protocol.toLowerCase() === 'onvif'; }
  async testStream(_input: { streamUrl: string; username?: string; password?: string; timeoutMs: number }): Promise<ConnectionVerificationResult> {
    return { status: 'FAILED', failureCode: 'DISCOVERY_UNAVAILABLE', retryable: true, supportRecommended: false, protocol: 'ONVIF', message: 'ONVIF discovery must run through a paired Sentira Edge Connector.', durationMs: 0 };
  }
}
