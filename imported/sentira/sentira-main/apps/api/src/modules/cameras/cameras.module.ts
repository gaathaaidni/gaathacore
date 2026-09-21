import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Camera } from '../../entities/camera.entity';
import { Connector } from '../../entities/connector.entity';
import { DiscoveredCamera } from '../../entities/discovered-camera.entity';
import { CameraOnboardingSession } from '../../entities/camera-onboarding-session.entity';
import { AuditLog } from '../../entities/audit-log.entity';
import { Organization } from '../../entities/organization.entity';
import { Role } from '../../entities/role.entity';
import { Site } from '../../entities/site.entity';
import { CamerasService } from './cameras.service';
import { CamerasController } from './cameras.controller';
import { CommonModule } from '../common/common.module';
import { CameraEntitlementService } from './camera-entitlement.service';
import { CameraOnboardingService } from './camera-onboarding.service';

@Module({
  imports: [TypeOrmModule.forFeature([Camera, Organization, Role, Site, Connector, DiscoveredCamera, CameraOnboardingSession, AuditLog]), CommonModule],
  providers: [CamerasService, CameraEntitlementService, CameraOnboardingService],
  controllers: [CamerasController],
  exports: [CamerasService],
})
export class CamerasModule {}