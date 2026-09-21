import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Camera } from '../../entities/camera.entity';
import { Site } from '../../entities/site.entity';
import { CreateCameraDto } from './dto/create-camera.dto';
import { EncryptionService } from '../common/encryption.service';
import { CameraEntitlementService } from './camera-entitlement.service';

@Injectable()
export class CamerasService {
  constructor(
    @InjectRepository(Camera)
    private camerasRepository: Repository<Camera>,
    private readonly encryptionService: EncryptionService,
    private readonly entitlement: CameraEntitlementService,
    @InjectRepository(Site) private readonly sitesRepository: Repository<Site>,
  ) {}

  private publicCamera(camera: Camera): Camera {
    const publicCamera = { ...camera };
    delete publicCamera.passwordEncrypted;
    delete publicCamera.streamUrl;
    delete publicCamera.username;
    return publicCamera;
  }

  async create(organizationId: string, createCameraDto: CreateCameraDto): Promise<Camera> {
    let streamUrl: URL;
    try { streamUrl = new URL(createCameraDto.streamUrl); } catch { throw new BadRequestException('Invalid stream URL'); }
    if (streamUrl.username || streamUrl.password || !['rtsp', 'http', 'https'].includes(streamUrl.protocol.replace(':', ''))) {
      throw new BadRequestException('Invalid stream URL');
    }
    if (this.isPrivateStreamTarget(streamUrl.hostname)) {
      throw new BadRequestException('Local cameras must connect through a Sentira Connector.');
    }
    const site = await this.sitesRepository.findOneBy({ id: createCameraDto.siteId, organizationId });
    if (!site) throw new NotFoundException('Site not found');
    const existing = await this.camerasRepository.findOne({ where: { organizationId, siteId: createCameraDto.siteId, streamUrl: createCameraDto.streamUrl } });
    if (existing) return this.publicCamera(existing);
    const { password, ...restOfDto } = createCameraDto;

    const cameraData: Partial<Camera> = {
      ...restOfDto,
      organizationId,
    };

    if (password) {
      cameraData.passwordEncrypted = this.encryptionService.encrypt(password);
    }

    const savedCamera = await this.entitlement.withCameraSlot(organizationId, async (manager) => manager.getRepository(Camera).save(cameraData));

    return this.publicCamera(savedCamera);
  }

  private isPrivateStreamTarget(hostname: string): boolean {
    const host = hostname.toLowerCase().replace(/^\[|\]$/g, '');
    if (host === 'localhost' || host.endsWith('.local') || host === '::1' || host.startsWith('127.') || host.startsWith('169.254.') || host.startsWith('10.') || host.startsWith('192.168.')) return true;
    const parts = host.split('.').map(Number);
    return parts.length === 4 && parts.every((part) => Number.isInteger(part) && part >= 0 && part <= 255) && parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31;
  }

  async findByOrganization(organizationId: string): Promise<Camera[]> { return (await this.camerasRepository.find({ where: { organizationId } })).map((camera) => this.publicCamera(camera)); }

  async findById(id: string, organizationId: string): Promise<Camera | null> {
    const camera = await this.camerasRepository.findOne({
      where: { id, organizationId },
    });
    return camera ? this.publicCamera(camera) : null;
  }

  async findBySite(siteId: string, organizationId: string): Promise<Camera[]> {
    const cameras = await this.camerasRepository.find({
      where: { siteId, organizationId },
    });
    return cameras.map((camera) => this.publicCamera(camera));
  }

  /**
   * Secure method for internal services to get all camera configs, including decrypted passwords.
   */
  async findAllInternal(): Promise<Camera[]> {
    const cameras = await this.camerasRepository.find();
    return cameras.map((camera) => {
      if (camera.passwordEncrypted) {
        camera['password'] = this.encryptionService.decrypt(camera.passwordEncrypted);
      }
      return camera;
    });
  }

  /**
   * Secure method for internal services to get full camera config, including decrypted password.
   */
  async getDecryptedCamera(id: string, organizationId: string): Promise<Camera | null> {
    const camera = await this.camerasRepository.findOne({ where: { id, organizationId } });
    if (camera && camera.passwordEncrypted) {
      (camera as any).password = this.encryptionService.decrypt(camera.passwordEncrypted);
    }
    return camera;
  }

  async updateStatus(id: string, status: string, organizationId: string): Promise<Camera> {
    await this.camerasRepository.update(
      { id, organizationId },
      { status: status as any },
    );
    const camera = await this.findById(id, organizationId);
    if (!camera) throw new NotFoundException('Camera not found');
    return camera;
  }
}
