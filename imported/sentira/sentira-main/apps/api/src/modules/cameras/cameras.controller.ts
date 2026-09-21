import { Body, Controller, ForbiddenException, Get, Headers, NotFoundException, Param, Post, UseGuards } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { CamerasService } from './cameras.service';
import { CreateCameraDto } from './dto/create-camera.dto';
import { ManualCameraOnboardingDto } from './dto/manual-camera-onboarding.dto';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';
import { PermissionGuard } from '../../auth/guards/permission.guard';
import { RequirePermission } from '../../auth/decorators/require-permission.decorator';
import { CameraOnboardingService } from './camera-onboarding.service';
import { CreateOnboardingSessionDto, PairConnectorDto, ClaimDiscoveredCameraBodyDto, RegisterConnectorDto, ReportDiscoveredCameraDto } from './dto/onboarding.dto';

@Controller('api/cameras')
export class CamerasController {
  constructor(
    private readonly camerasService: CamerasService,
    private readonly configService: ConfigService,
    private readonly onboardingService?: CameraOnboardingService,
  ) {}

  @Post('onboarding/sessions')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  createOnboardingSession(@Body() dto: CreateOnboardingSessionDto, @CurrentUser() user: CurrentUserDto) {
    return this.onboardingService!.createSession(user.organizationId, user.id, dto);
  }

  @Get('onboarding/sessions/:id')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  getOnboardingSession(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.onboardingService!.getSession(user.organizationId, id);
  }

  @Post('onboarding/sessions/:id/pair')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  pairConnector(@Param('id') id: string, @Body() dto: PairConnectorDto, @CurrentUser() user: CurrentUserDto) {
    return this.onboardingService!.pairConnector(user.organizationId, id, dto, user.id);
  }

  @Get('onboarding/sessions/:id/discovered-cameras')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  listDiscovered(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    return this.onboardingService!.listDiscovered(user.organizationId, id);
  }

  @Post('onboarding/discovered-cameras/:id/claim')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  claimDiscovered(@Param('id') id: string, @Body() dto: ClaimDiscoveredCameraBodyDto, @CurrentUser() user: CurrentUserDto) {
    return this.onboardingService!.claim(user.organizationId, user.id, { ...dto, discoveredCameraId: id });
  }

  @Post('connectors/register')
  registerConnector(@Body() dto: RegisterConnectorDto) { return this.onboardingService!.registerConnector(dto); }

  @Post('connectors/:id/heartbeat')
  heartbeat(@Param('id') id: string, @Headers('x-connector-token') token?: string) {
    return this.onboardingService!.heartbeat(id, token || '');
  }

  @Post('connectors/:id/discovered-cameras')
  reportDiscovered(@Param('id') id: string, @Headers('x-connector-token') token: string | undefined, @Body() dto: ReportDiscoveredCameraDto) {
    return this.onboardingService!.reportDiscovered(id, token || '', dto);
  }

  @Post()
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  async create(@Body() createCameraDto: CreateCameraDto, @CurrentUser() user: CurrentUserDto) {
    return this.camerasService.create(user.organizationId, createCameraDto);
  }

  /** Simple user-facing setup contract. Advanced protocol details stay out of the normal UI. */
  @Post('onboarding/manual')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  async manualOnboarding(@Body() dto: ManualCameraOnboardingDto, @CurrentUser() user: CurrentUserDto) {
    return this.camerasService.create(user.organizationId, { ...dto, protocol: 'rtsp' });
  }

  @Get()
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  async findAll(@CurrentUser() user: CurrentUserDto) { return this.camerasService.findByOrganization(user.organizationId); }

  @Get('site/:siteId')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  async findBySite(@Param('siteId') siteId: string, @CurrentUser() user: CurrentUserDto) {
    return this.camerasService.findBySite(siteId, user.organizationId);
  }

  @Get(':id/status')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  async status(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    const camera = await this.camerasService.findById(id, user.organizationId);
    if (!camera) throw new NotFoundException('Camera not found');
    return { id: camera.id, status: camera.status, aiProcessingStatus: camera.aiProcessingStatus, lastHeartbeatAt: camera.lastHeartbeatAt ?? null, diagnosticAt: new Date().toISOString() };
  }

  @Get(':id')
  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  async findById(@Param('id') id: string, @CurrentUser() user: CurrentUserDto) {
    const camera = await this.camerasService.findById(id, user.organizationId);
    if (!camera) throw new NotFoundException('Camera not found');
    return camera;
  }

  @Get('internal/all')
  async findAllInternal(@Headers('x-internal-token') internalToken?: string) {
    const expectedToken = this.configService.get<string>('STREAM_GATEWAY_INTERNAL_TOKEN');
    if (!expectedToken || internalToken !== expectedToken) {
      throw new ForbiddenException('Invalid internal token');
    }

    return this.camerasService.findAllInternal();
  }
}
