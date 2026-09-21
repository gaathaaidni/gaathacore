import { ConflictException, Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { DataSource, Repository } from 'typeorm';
import { Organization } from '../../entities/organization.entity';
import { cameraLimitMessage, CAMERA_LIMIT_REACHED, FREE_PLAN } from '../../common/entitlements';

export function canCreateCamera(cameraCount: number, cameraLimit: number): boolean {
  return cameraCount < cameraLimit;
}

@Injectable()
export class CameraEntitlementService {
  constructor(@InjectRepository(Organization) private readonly organizations: Repository<Organization>, private readonly dataSource: DataSource) {}

  async withCameraSlot<T>(organizationId: string, operation: (manager: ReturnType<DataSource['createQueryRunner']>['manager']) => Promise<T>): Promise<T> {
    return this.dataSource.transaction(async (manager) => {
      const organization = await manager.getRepository(Organization).findOne({ where: { id: organizationId }, lock: { mode: 'pessimistic_write' } });
      if (!organization) throw new ConflictException({ code: 'ORGANIZATION_NOT_FOUND', message: 'Organization not found' });
      const count = await manager.getRepository('cameras').count({ where: { organizationId } });
      if (!canCreateCamera(count, organization.cameraLimit)) throw new ConflictException({ code: CAMERA_LIMIT_REACHED, message: cameraLimitMessage(organization.plan ?? FREE_PLAN, organization.cameraLimit) });
      return operation(manager);
    });
  }
}