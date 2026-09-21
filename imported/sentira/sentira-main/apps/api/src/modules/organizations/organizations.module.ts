import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { OrganizationsService } from './organizations.service';
import { OrganizationsController } from './organizations.controller';
import { Organization } from '../../entities/organization.entity';
import { Site } from '../../entities/site.entity';
import { Event } from '../../entities/event.entity';
import { Camera } from '../../entities/camera.entity';
import { Rule } from '../../entities/rule.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([Organization, Site, Event, Camera, Rule]),
  ],
  controllers: [OrganizationsController],
  providers: [OrganizationsService],
  exports: [OrganizationsService],
})
export class OrganizationsModule {}