import { Injectable, InternalServerErrorException, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectRepository } from '@nestjs/typeorm';
import { randomUUID } from 'crypto';
import { JwtService } from '@nestjs/jwt';
import { Repository } from 'typeorm';
import { Camera } from '../../entities/camera.entity';
import { Site } from '../../entities/site.entity';
import { CurrentUserDto } from '../../auth/auth.dto';

export type StreamOperation = 'playback' | 'status' | 'start' | 'stop';

@Injectable()
export class StreamAuthorizationService {
  constructor(
    @InjectRepository(Camera) private readonly cameras: Repository<Camera>,
    @InjectRepository(Site) private readonly sites: Repository<Site>,
    private readonly config: ConfigService,
  ) {}

  async issue(user: CurrentUserDto, cameraId: string, operation: StreamOperation, requestId?: string) {
    const camera = await this.cameras.findOne({ where: { id: cameraId, organizationId: user.organizationId } });
    if (!camera) throw new NotFoundException('Camera not found');
    const site = await this.sites.findOne({ where: { id: camera.siteId, organizationId: user.organizationId } });
    if (!site) throw new NotFoundException('Camera site not found');

    const secret = this.config.get<string>('STREAM_GATEWAY_AUTH_SECRET')?.trim();
    if (!secret || secret.length < 32) {
      throw new InternalServerErrorException('Stream authorization is not configured');
    }

    const now = Math.floor(Date.now() / 1000);
    const expiresAt = now + 60;
    const token = await new JwtService({ secret }).signAsync({
      iss: 'sentira-api',
      aud: 'sentira-stream-gateway',
      sub: user.id,
      jti: randomUUID(),
      organizationId: camera.organizationId,
      siteId: camera.siteId,
      cameraId: camera.id,
      operation,
      requestId: requestId || randomUUID(),
      iat: now,
      exp: expiresAt,
    }, { algorithm: 'HS256' });

    return {
      authorizationToken: token,
      expiresAt: new Date(expiresAt * 1000).toISOString(),
      cameraId: camera.id,
      organizationId: camera.organizationId,
      siteId: camera.siteId,
      operation,
      gatewayPath: `/streams/${camera.id}/${operation}`,
    };
  }
}