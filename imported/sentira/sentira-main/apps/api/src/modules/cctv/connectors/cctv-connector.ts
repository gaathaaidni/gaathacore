export type ConnectionFailureCode =
  | 'CONNECTION_TIMEOUT'
  | 'AUTHENTICATION_FAILED'
  | 'STREAM_UNAVAILABLE'
  | 'INVALID_RTSP_URL'
  | 'DEVICE_UNREACHABLE'
  | 'UNSUPPORTED_PROTOCOL'
  | 'CONNECTOR_OFFLINE'
  | 'DISCOVERY_UNAVAILABLE';

export type ConnectionVerificationResult = {
  status: 'VERIFIED_CONNECTED' | 'FAILED';
  failureCode?: ConnectionFailureCode;
  retryable: boolean;
  supportRecommended: boolean;
  protocol: string;
  message: string;
  durationMs: number;
};

export interface CctvConnector {
  getId(): string;
  getName(): string;
  supports(deviceType: string): boolean;
  supportsProtocol(protocol: string): boolean;
  testStream(input: { streamUrl: string; username?: string; password?: string; timeoutMs: number }): Promise<ConnectionVerificationResult>;
}
