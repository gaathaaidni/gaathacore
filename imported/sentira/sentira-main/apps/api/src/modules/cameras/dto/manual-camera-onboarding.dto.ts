import { IsNotEmpty, IsOptional, IsString, IsUUID } from 'class-validator';

/** Explicit onboarding contract for the user-facing camera setup flow. */
export class ManualCameraOnboardingDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @IsUUID()
  siteId: string;

  @IsString()
  @IsNotEmpty()
  streamUrl: string;

  @IsOptional()
  @IsString()
  username?: string;

  @IsOptional()
  @IsString()
  password?: string;
}
