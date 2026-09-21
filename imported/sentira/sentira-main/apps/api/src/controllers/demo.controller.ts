import { Controller, Post, Body, UseGuards, BadRequestException } from '@nestjs/common';
import { EventGeneratorService } from '../services/event-generator.service';
import { RuleEngineService } from '../services/rule-engine.service';
import { NotificationService } from '../services/notification.service';
import { RulesService } from '../modules/rules/rules.service';
import { CamerasService } from '../modules/cameras/cameras.service';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../auth/auth.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { EventsGateway } from '../events.gateway';

@Controller('api/demo')
@UseGuards(JwtAuthGuard)
export class DemoController {
  constructor(
    private eventGeneratorService: EventGeneratorService,
    private ruleEngineService: RuleEngineService,
    private notificationService: NotificationService,
    private rulesService: RulesService,
    private camerasService: CamerasService,
    private eventsGateway: EventsGateway,
  ) {}

  @Post('generate-event')
  async generateEvent(
    @Body() body: { cameraId: string; ruleId: string },
    @CurrentUser() user: CurrentUserDto,
  ) {
    try {
      // Get camera and rule
      const camera = await this.camerasService.findById(body.cameraId, user.organizationId);
      if (!camera) {
        throw new BadRequestException('Camera not found');
      }

      const rule = await this.rulesService.findById(body.ruleId, user.organizationId);
      if (!rule) {
        throw new BadRequestException('Rule not found');
      }

      // Generate demo event
      const event = await this.eventGeneratorService.createEventFromDetections(
        user.organizationId,
        camera.siteId,
        body.cameraId,
        body.ruleId,
        rule.ruleType,
        rule.status === 'active' ? 'high' : 'medium',
        0.87,
      );

      // Send notification
      await this.notificationService.notifyEvent(
        { ...event, camera } as any,
        `Demo: ${rule.name} triggered on ${camera.name}`,
      );

      // Broadcast the event via WebSocket
      this.eventsGateway.broadcastEventCreated(event);

      return {
        success: true,
        event,
        message: 'Demo event created and notification sent',
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new BadRequestException(message);
    }
  }

  @Post('trigger-all-rules')
  async triggerAllRules(@CurrentUser() user: CurrentUserDto) {
    try {
      const rules = await this.rulesService.findByOrganization(user.organizationId);
      const events = [];

      for (const rule of rules) {
        if (this.ruleEngineService.evaluateDemoRules(rule) && rule.cameraId) {
          const camera = await this.camerasService.findById(rule.cameraId, user.organizationId);
          if (camera) {
            const event = await this.eventGeneratorService.createEventFromDetections(
              user.organizationId,
              camera.siteId,
              camera.id,
              rule.id,
              rule.ruleType,
              'medium',
              0.85,
            );

            await this.notificationService.notifyEvent(
              { ...event, camera } as any,
              `${rule.name} triggered on ${camera.name}`,
            );

            // Broadcast the event via WebSocket
            this.eventsGateway.broadcastEventCreated(event);

            events.push(event);
          }
        }
      }

      return {
        success: true,
        eventsCreated: events.length,
        events,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new BadRequestException(message);
    }
  }

}
