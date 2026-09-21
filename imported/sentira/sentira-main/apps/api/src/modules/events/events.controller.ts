import { Controller, Get, Post, Body, Param, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { EventsService } from './events.service';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';
import { RequirePermission } from '../../auth/decorators/require-permission.decorator';
import { PermissionGuard } from '../../auth/guards/permission.guard';
import { EvidenceService } from '../../services/evidence.service';

@Controller('api/events')
@UseGuards(JwtAuthGuard, PermissionGuard)
export class EventsController {
  constructor(private eventsService: EventsService, private evidence: EvidenceService) {}

  @Get()
  @RequirePermission('event.view') async findAll(@CurrentUser() user: CurrentUserDto) {
    return this.eventsService.findByOrganization(user.organizationId);
  }

  @Get(':id')
  @RequirePermission('event.view') async findById(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.eventsService.findById(id, user.organizationId);
  }

  @Post(':id/acknowledge')
  @RequirePermission('event.acknowledge') async acknowledge(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.eventsService.updateStatus(id, 'acknowledged', user.organizationId, user.id);
  }

  @Post(':id/resolve')
  @RequirePermission('event.resolve') async resolve(@Param('id') id: string, @Body() body: { resolutionReason?: string }, @CurrentUser() user: CurrentUserDto) {
    return this.eventsService.updateStatus(id, 'resolved', user.organizationId, user.id, body);
  }

  @Post(':id/dismiss')
  @RequirePermission('event.dismiss') async dismiss(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.eventsService.updateStatus(id, 'dismissed', user.organizationId, user.id);
  }

  @Get(':eventId/media/:mediaId')
  @RequirePermission('event.view')
  async readMedia(@Param('eventId') eventId: string, @Param('mediaId') mediaId: string, @CurrentUser() user: CurrentUserDto, @Res() response: Response) {
    const { media, bytes } = await this.evidence.readAuthorized(mediaId, eventId, user.organizationId);
    response.setHeader('Content-Type', media.contentType ?? 'application/octet-stream');
    response.setHeader('Content-Length', String(bytes.length)); response.setHeader('Cache-Control', 'private, no-store'); response.send(bytes);
  }
}
