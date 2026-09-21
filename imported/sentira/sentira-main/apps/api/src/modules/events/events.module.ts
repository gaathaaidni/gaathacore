import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Event } from '../../entities/event.entity';
import { EventMedia } from '../../entities/event-media.entity';
import { AuditLog, Role } from '../../entities';
import { PermissionGuard } from '../../auth/guards/permission.guard';
import { EventsService } from './events.service';
import { EventsController } from './events.controller';
import { EvidenceService } from '../../services/evidence.service';
import { ObjectStorageService } from '../../services/object-storage.service';

@Module({
  imports: [TypeOrmModule.forFeature([Event, EventMedia, AuditLog, Role])],
  providers: [EventsService, PermissionGuard, EvidenceService, ObjectStorageService],
  controllers: [EventsController],
  exports: [EventsService],
})
export class EventsModule {}
