import { Controller, Get, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';
import { OrganizationsService } from '../organizations/organizations.service';

@Controller('api/dashboard')
@UseGuards(JwtAuthGuard)
export class DashboardController {
  constructor(private readonly orgService: OrganizationsService) {}

  @Get('stats')
  async getStats(@CurrentUser() user: CurrentUserDto) {
    return this.orgService.getDashboardStats(user.organizationId);
  }
}