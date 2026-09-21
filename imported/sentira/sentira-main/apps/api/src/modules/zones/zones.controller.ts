import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { ZonesService } from './zones.service';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';

@Controller('api/zones')
@UseGuards(JwtAuthGuard)
export class ZonesController {
  constructor(private zonesService: ZonesService) {}

  @Post()
  async create(@Body() zoneData: any, @CurrentUser() user: CurrentUserDto) {
    return this.zonesService.create(user.organizationId, zoneData);
  }

  @Get(':id')
  async findById(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.zonesService.findById(id, user.organizationId);
  }

  @Get('camera/:cameraId')
  async findByCamera(@Param('cameraId') cameraId: string, @CurrentUser() user: CurrentUserDto) {
    return this.zonesService.findByCamera(cameraId, user.organizationId);
  }
}
