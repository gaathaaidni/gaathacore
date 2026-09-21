import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { RulesService } from './rules.service';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';

@Controller('api/rules')
@UseGuards(JwtAuthGuard)
export class RulesController {
  constructor(private rulesService: RulesService) {}

  @Get()
  async findAll(@CurrentUser() user: CurrentUserDto) {
    return this.rulesService.findByOrganization(user.organizationId);
  }

  @Get(':id')
  async findById(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.rulesService.findById(id, user.organizationId);
  }

  @Post()
  async create(@Body() ruleData: any, @CurrentUser() user: CurrentUserDto) {
    return this.rulesService.create(user.organizationId, {
      ...ruleData,
      createdBy: user.id,
    });
  }
}
