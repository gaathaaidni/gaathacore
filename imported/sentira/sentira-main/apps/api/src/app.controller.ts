import { Controller, Get, UseGuards } from '@nestjs/common';
import { AppService } from './app.service';
import { HealthService } from './services/health.service';
import { JwtAuthGuard } from './auth/guards/jwt-auth.guard';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService, private readonly healthService: HealthService) {}

  @Get('/health')
  getHealth() { return this.appService.getHealth(); }

  @Get('/api/health')
  getApiHealth() { return this.appService.getHealth(); }

  @Get('/ready')
  getReady() { return this.appService.getReady(); }

  @Get('/api/system/health')
  @UseGuards(JwtAuthGuard)
  getSystemHealth() { return this.healthService.getSystemHealth(); }
}
