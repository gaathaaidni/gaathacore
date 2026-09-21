import { IsString, IsOptional, IsUUID, IsNumber, IsNotEmpty } from 'class-validator';

export class CreateCameraDto {
  @IsString()
  name: string;

  @IsUUID()
  siteId: string;

  @IsString()
  @IsNotEmpty()
  streamUrl: string;

  @IsString()
  protocol: 'rtsp' | 'http' | 'https';

  @IsOptional()
  @IsString()
  username?: string;

  @IsOptional()
  @IsString()
  password?: string;

  @IsOptional()
  @IsString()
  location?: string;

  @IsOptional()
  @IsString()
  resolution?: string;

  @IsOptional()
  @IsNumber()
  fps?: number;
}
