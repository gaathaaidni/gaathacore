import { IsIn, IsOptional, IsString, IsUUID, MaxLength, MinLength } from 'class-validator';

export class CreateOnboardingSessionDto {
  @IsIn(['automatic', 'qr', 'dvr_nvr'])
  method: 'automatic' | 'qr' | 'dvr_nvr';
}

export class PairConnectorDto {
  @IsString()
  @MinLength(6)
  @MaxLength(64)
  pairingCode: string;

  @IsString()
  @MinLength(1)
  @MaxLength(255)
  connectorName: string;
}

export class ClaimDiscoveredCameraDto {
  @IsUUID()
  discoveredCameraId: string;

  @IsUUID()
  siteId: string;

  @IsString()
  @MinLength(1)
  @MaxLength(255)
  name: string;
}

export class ClaimDiscoveredCameraBodyDto {
  @IsUUID() siteId: string;
  @IsString() @MinLength(1) @MaxLength(255) name: string;
}

export class RegisterConnectorDto {
  @IsUUID()
  sessionId: string;

  @IsString()
  @MinLength(6)
  @MaxLength(64)
  pairingCode: string;

  @IsString()
  @MinLength(1)
  @MaxLength(255)
  name: string;

  @IsOptional()
  @IsString()
  @MaxLength(64)
  version?: string;
}

export class ReportDiscoveredCameraDto {
  @IsString() @MinLength(1) @MaxLength(255) name: string;
  @IsOptional() @IsString() @MaxLength(255) localAddress?: string;
  @IsOptional() @IsString() @MaxLength(100) manufacturer?: string;
  @IsOptional() @IsString() @MaxLength(100) model?: string;
  @IsOptional() @IsString() @MaxLength(50) protocol?: string;
}
