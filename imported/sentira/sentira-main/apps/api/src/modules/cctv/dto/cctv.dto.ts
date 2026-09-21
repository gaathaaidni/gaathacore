import { ArrayMaxSize, IsArray, IsIn, IsInt, IsObject, IsOptional, IsString, IsUUID, Max, MaxLength, Min, MinLength } from 'class-validator';

export class CreateSetupSessionDto {
  @IsOptional() @IsIn(['WIFI_CAMERA', 'IP_CAMERA', 'DVR', 'NVR', 'CAMERA_SYSTEM', 'OTHER']) deviceType?: string;
  @IsOptional() @IsUUID() siteId?: string;
}

export class UpdateSetupSessionDto {
  @IsOptional() @IsIn(['WIFI_CAMERA', 'IP_CAMERA', 'DVR', 'NVR', 'CAMERA_SYSTEM', 'OTHER']) deviceType?: string;
  @IsOptional() @IsUUID() siteId?: string;
  @IsOptional() @IsUUID() manufacturerId?: string;
  @IsOptional() @IsUUID() modelId?: string;
  @IsOptional() @IsUUID() guideId?: string;
  @IsOptional() @IsString() @MaxLength(120) currentStep?: string;
  @IsOptional() @IsObject() answers?: Record<string, unknown>;
}

export class TestSetupSessionDto {
  @IsOptional() @IsUUID() cameraId?: string;
  @IsOptional() @IsIn(['rtsp', 'onvif']) protocol?: string;
  @IsOptional() @IsString() @MaxLength(2048) streamUrl?: string;
  @IsOptional() @IsString() @MaxLength(255) username?: string;
  @IsOptional() @IsString() @MaxLength(255) password?: string;
}

export class CompleteSetupSessionDto {
  @IsUUID()
  cameraId: string;
}

export class DiscoverSetupSessionDto {
  @IsOptional() @IsInt() @Min(1000) @Max(30000) maxDurationMs?: number;
}

export class EnumerateChannelsDto {
  @IsUUID() connectorId: string;
  @IsUUID() recorderId: string;
  @IsOptional() @IsInt() @Min(1) @Max(64) maxChannels?: number;
}

export class CreateSupportRequestDto {
  @IsOptional() @IsUUID() setupSessionId?: string;
  @IsOptional() @IsUUID() siteId?: string;
  @IsOptional() @IsUUID() cameraId?: string;
  @IsIn(['SETUP_HELP', 'CAMERA_INCOMPATIBILITY', 'DVR_SETUP', 'NVR_SETUP', 'NETWORK_ISSUE', 'AUTHENTICATION', 'STREAM_ISSUE', 'DISCOVERY_FAILURE', 'OTHER']) reason: string;
  @IsOptional() @IsIn(['LOW', 'NORMAL', 'HIGH', 'CRITICAL']) priority?: string;
  @IsOptional() @IsString() @MaxLength(2000) message?: string;
  @IsOptional() @IsObject() context?: Record<string, unknown>;
}

export class CreateManufacturerDto {
  @IsString() @MinLength(1) @MaxLength(120) name: string;
  @IsString() @MinLength(1) @MaxLength(140) slug: string;
  @IsOptional() @IsString() @MaxLength(5000) description?: string;
  @IsOptional() @IsString() @MaxLength(500) websiteUrl?: string;
}

export class CreateModelDto {
  @IsUUID() manufacturerId: string;
  @IsString() @MinLength(1) @MaxLength(160) modelNumber: string;
  @IsString() @MinLength(1) @MaxLength(180) name: string;
  @IsString() @MinLength(1) @MaxLength(180) slug: string;
  @IsString() @MaxLength(40) deviceType: string;
  @IsOptional() @IsString() @MaxLength(5000) description?: string;
  @IsOptional() @IsArray() supportedProtocols?: Array<Record<string, unknown>>;
  @IsOptional() @IsArray() discoveryMethods?: string[];
}

export class CreateGuideDto {
  @IsOptional() @IsUUID() manufacturerId?: string;
  @IsOptional() @IsUUID() modelId?: string;
  @IsString() @MinLength(1) @MaxLength(180) title: string;
  @IsString() @MinLength(1) @MaxLength(5000) description: string;
  @IsOptional() @IsArray() steps?: Array<Record<string, unknown>>;
  @IsOptional() @IsArray() troubleshooting?: Array<Record<string, unknown>>;
  @IsOptional() @IsString() @MaxLength(80) verificationStatus?: string;
}

// Edge Connector Pairing & Discovery
export class PairConnectorDto {
  @IsString() @MinLength(6) @MaxLength(32) pairingCode: string;
  @IsString() @MinLength(1) @MaxLength(255) connectorName: string;
  @IsOptional() @IsString() @MaxLength(64) version?: string;
}

export class HeartbeatConnectorDto {
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
  @IsOptional() @IsObject() metadata?: Record<string, unknown>;
}

export class DiscoverCamerasDto {
  @IsUUID() setupSessionId: string;
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
  @IsOptional() @IsInt() @Min(1000) @Max(60000) maxDurationMs?: number;
}

export class ReportDiscoveryResultsDto {
  @IsUUID() setupSessionId: string;
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
  @IsArray() @ArrayMaxSize(64) results: Array<{
    name: string;
    manufacturer?: string;
    model?: string;
    localAddress?: string;
    protocol?: string;
    capabilities?: Record<string, unknown>;
    discoveryStatus?: 'READY' | 'UNSUPPORTED' | 'UNAVAILABLE';
  }>;
}

export class DiscoveredCameraResultDto {
  id: string;
  name: string;
  manufacturer?: string;
  model?: string;
  protocol?: string;
  capabilities?: Record<string, unknown>;
  localAddress?: string;
  discoveryStatus: 'READY' | 'UNSUPPORTED' | 'UNAVAILABLE';
}

export class CreateConnectorCommandDto {
  @IsUUID() connectorId: string;
  @IsIn(['PING', 'GET_CAPABILITIES', 'DISCOVER_ONVIF', 'GET_ONVIF_DEVICE_INFORMATION', 'GET_ONVIF_MEDIA_PROFILES', 'GET_ONVIF_STREAM_URI', 'VERIFY_ONVIF_DEVICE', 'TEST_RTSP']) commandType: string;
  @IsOptional() @IsObject() payload?: Record<string, unknown>;
  @IsOptional() @IsString() @MaxLength(64) correlationId?: string;
  @IsOptional() @IsString() @MaxLength(128) idempotencyKey?: string;
  @IsOptional() @IsInt() @Min(1) @Max(10) maxAttempts?: number;
  @IsOptional() @IsInt() @Min(1) @Max(3600) expiresInSeconds?: number;
}

export class PollConnectorCommandsDto {
  @IsOptional() @IsUUID() connectorId?: string;
  @IsOptional() @IsString() @MaxLength(512) registrationToken?: string;
  @IsOptional() @IsInt() @Min(1) @Max(20) limit?: number;
  @IsOptional() @IsInt() @Min(0) @Max(20) wait?: number;
}

export class AcknowledgeConnectorCommandDto {
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
}

export class ReportConnectorCommandResultDto {
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
  @IsOptional() @IsString() @MaxLength(80) status?: string;
  @IsOptional() @IsObject() result?: Record<string, unknown>;
  @IsOptional() @IsString() @MaxLength(80) errorCode?: string;
  @IsOptional() @IsString() @MaxLength(500) errorMessage?: string;
  @IsOptional() @IsString() @MaxLength(64) startedAt?: string;
  @IsOptional() @IsString() @MaxLength(64) completedAt?: string;
}

export class CancelConnectorCommandDto {
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
}

export class EnumerateRecorderChannelsDto {
  @IsUUID() connectorId: string;
  @IsString() @MaxLength(512) registrationToken: string;
  @IsUUID() recorderId: string;
  @IsOptional() @IsInt() @Min(1) @Max(64) maxChannels?: number;
  @IsOptional() @IsInt() @Min(1000) @Max(60000) timeoutMs?: number;
}

export class RecorderChannelDto {
  channelNumber: number;
  name?: string;
  available: boolean;
  protocol?: string;
  streamAvailable: boolean;
  verificationStatus: 'VERIFIED' | 'UNVERIFIED' | 'UNAVAILABLE';
}
