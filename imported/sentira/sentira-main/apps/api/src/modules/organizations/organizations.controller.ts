import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  UseGuards,
  NotFoundException,
} from '@nestjs/common';
import { OrganizationsService } from './organizations.service';
import { CreateSiteDto } from './dto';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';

@Controller('api/organizations')
@UseGuards(JwtAuthGuard)
export class OrganizationsController {
  constructor(private readonly organizationsService: OrganizationsService) {}

  @Get(':id')
  async findOne(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    if (id !== user.organizationId) {
      throw new NotFoundException('Organization not found');
    }
    const org = await this.organizationsService.findById(id);
    if (!org) {
      throw new NotFoundException('Organization not found');
    }
    return org;
  }

  @Get(':id/sites')
  getSites(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    if (id !== user.organizationId) throw new NotFoundException('Organization not found');
    return this.organizationsService.getSites(id);
  }

  @Post(':id/sites')
  createSite(@Param('id') id: string, @Body() createSiteDto: CreateSiteDto, @CurrentUser() user: CurrentUserDto) {
    if (id !== user.organizationId) throw new NotFoundException('Organization not found');
    return this.organizationsService.createSite(id, createSiteDto);
  }
}