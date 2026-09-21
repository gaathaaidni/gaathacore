import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Zone } from '../../entities/zone.entity';

@Injectable()
export class ZonesService {
  constructor(
    @InjectRepository(Zone)
    private zonesRepository: Repository<Zone>,
  ) {}

  async create(organizationId: string, zoneData: Partial<Zone>): Promise<Zone> {
    return this.zonesRepository.save({
      ...zoneData,
      organizationId,
    });
  }

  async findById(id: string, organizationId: string): Promise<Zone | null> {
    return this.zonesRepository.findOne({
      where: { id, organizationId },
    });
  }

  async findByCamera(cameraId: string, organizationId: string): Promise<Zone[]> {
    return this.zonesRepository.find({
      where: { cameraId, organizationId },
    });
  }

  async update(id: string, organizationId: string, zoneData: Partial<Zone>): Promise<Zone> {
    await this.zonesRepository.update(
      { id, organizationId },
      zoneData,
    );
    return this.findById(id, organizationId);
  }
}
