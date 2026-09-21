export type EdgeConnectorStatus = 'PENDING' | 'ONLINE' | 'OFFLINE' | 'DISABLED';

export type EdgeDiscoveryResult = {
  id: string;
  name: string;
  manufacturer?: string;
  model?: string;
  deviceType?: string;
  protocol?: string;
  capabilities?: Record<string, unknown>;
  localAddress?: string;
  discoveryStatus: 'READY' | 'UNSUPPORTED' | 'UNAVAILABLE';
};

export type EdgeRecorderChannel = {
  channelNumber: number;
  name?: string;
  available: boolean;
  protocol?: string;
  streamAvailable: boolean;
  verificationStatus: 'VERIFIED' | 'UNVERIFIED' | 'UNAVAILABLE';
};

export interface EdgeConnectorContract {
  register(pairingCode: string, name: string, version?: string): Promise<{ connectorId: string; registrationToken: string }>;
  heartbeat(connectorId: string, registrationToken: string): Promise<{ status: EdgeConnectorStatus; lastHeartbeatAt: string }>;
  discover(connectorId: string, registrationToken: string, input: { setupSessionId: string; maxDurationMs: number }): Promise<EdgeDiscoveryResult[]>;
  verifyDevice(connectorId: string, registrationToken: string, deviceId: string, input: { timeoutMs: number }): Promise<{ status: 'VERIFIED_CONNECTED' | 'FAILED'; failureCode?: string; message: string }>;
  enumerateChannels(connectorId: string, registrationToken: string, recorderId: string, input: { maxChannels: number; timeoutMs: number }): Promise<EdgeRecorderChannel[]>;
}
