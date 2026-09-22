import { Body, Controller, Get, Param, Patch, Post, Query, UseGuards } from '@nestjs/common';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { PermissionGuard } from '../../auth/guards/permission.guard';
import { RequirePermission } from '../../auth/decorators/require-permission.decorator';
import { CctvService } from './cctv.service';
import { AcknowledgeConnectorCommandDto, CancelConnectorCommandDto, CompleteSetupSessionDto, CreateConnectorCommandDto, CreateGuideDto, CreateManufacturerDto, CreateModelDto, CreateSetupSessionDto, CreateSupportRequestDto, DiscoverCamerasDto, EnumerateRecorderChannelsDto, HeartbeatConnectorDto, PairConnectorDto, PollConnectorCommandsDto, ReportConnectorCommandResultDto, ReportDiscoveryResultsDto, TestSetupSessionDto, UpdateSetupSessionDto } from './dto/cctv.dto';

@Controller('api/cctv')
export class CctvController {
  constructor(private readonly service: CctvService) {}

  @Get('manufacturers') listManufacturers(@Query('search') search?: string) { return this.service.listManufacturers(search); }
  @Get('manufacturers/:id/models') listModels(@Param('id') id: string, @Query('search') search?: string) { return this.service.listModels(id, search); }
  @Get('models/:id') getModel(@Param('id') id: string) { return this.service.getModel(id); }
  @Get('models/:id/guides') listModelGuides(@Param('id') id: string) { return this.service.listGuides(id); }
  @Get('help/search') searchHelp(@Query('q') query: string) { return this.service.searchHelp(query); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('setup-sessions') createSession(@CurrentUser() user: CurrentUserDto, @Body() dto: CreateSetupSessionDto) { return this.service.createSession(user, dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('setup-sessions/:id/connector-pairing') createConnectorPairing(@CurrentUser() user: CurrentUserDto, @Param('id') id: string) { return this.service.createConnectorPairing(user, id); }

  @Post('setup-sessions/:id/connector/register') registerConnector(@Param('id') id: string, @Body() dto: PairConnectorDto) { return this.service.registerConnector(id, dto); }

  @Post('connectors/heartbeat') heartbeatConnector(@Body() dto: HeartbeatConnectorDto) { return this.service.heartbeatConnector(dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('connectors/:id/revoke') revokeConnector(@CurrentUser() user: CurrentUserDto, @Param('id') id: string) { return this.service.revokeConnector(user, id); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('connectors/:id/rotate') rotateConnectorToken(@CurrentUser() user: CurrentUserDto, @Param('id') id: string) { return this.service.rotateConnectorToken(user, id); }

  @Post('connectors/discover') discoverThroughConnector(@Body() dto: DiscoverCamerasDto) { return this.service.discoverThroughConnector(dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('connectors/:id/commands') createConnectorCommand(@CurrentUser() user: CurrentUserDto, @Param('id') id: string, @Body() dto: CreateConnectorCommandDto) { return this.service.createConnectorCommand(user, { ...dto, connectorId: id }); }

  @Get('connectors/me/commands') pollConnectorCommands(@Query() dto: PollConnectorCommandsDto) { return this.service.getConnectorCommandsForPolling(dto.connectorId || '', dto.registrationToken || '', dto.limit || 5, dto.wait || 0); }

  @Post('connectors/me/commands/:commandId/ack') acknowledgeConnectorCommand(@Param('commandId') commandId: string, @Body() dto: AcknowledgeConnectorCommandDto) { return this.service.acknowledgeConnectorCommand(dto.connectorId, dto.registrationToken, commandId); }

  @Post('connectors/me/commands/:commandId/result') reportConnectorCommandResult(@Param('commandId') commandId: string, @Body() dto: ReportConnectorCommandResultDto) { return this.service.reportConnectorCommandResult(dto.connectorId, dto.registrationToken, commandId, dto); }

  @Post('connectors/me/commands/:commandId/cancel') cancelConnectorCommand(@Param('commandId') commandId: string, @Body() dto: CancelConnectorCommandDto) { return this.service.cancelConnectorCommand(dto.connectorId, dto.registrationToken, commandId); }

  @Post('connectors/discovery-results') reportDiscoveryResults(@Body() dto: ReportDiscoveryResultsDto) { return this.service.reportDiscoveryResults(dto); }

  @Post('connectors/recorder-channels') enumerateConnectorChannels(@Body() dto: EnumerateRecorderChannelsDto) { return this.service.enumerateConnectorChannels(dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  @Get('setup-sessions/active') getActiveSession(@CurrentUser() user: CurrentUserDto) { return this.service.getActiveSession(user); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  @Get('setup-sessions/:id') getSession(@CurrentUser() user: CurrentUserDto, @Param('id') id: string) { return this.service.getSession(user, id); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Patch('setup-sessions/:id') updateSession(@CurrentUser() user: CurrentUserDto, @Param('id') id: string, @Body() dto: UpdateSetupSessionDto) { return this.service.updateSession(user, id, dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('setup-sessions/:id/test') testSession(@CurrentUser() user: CurrentUserDto, @Param('id') id: string, @Body() dto: TestSetupSessionDto) { return this.service.testSession(user, id, dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  @Get('setup-sessions/:id/tests') listTests(@CurrentUser() user: CurrentUserDto, @Param('id') id: string) { return this.service.listTests(user, id); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('setup-sessions/:id/complete') completeSession(@CurrentUser() user: CurrentUserDto, @Param('id') id: string, @Body() dto: CompleteSetupSessionDto) { return this.service.completeSession(user, id, dto.cameraId); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.create')
  @Post('support-requests') createSupportRequest(@CurrentUser() user: CurrentUserDto, @Body() dto: CreateSupportRequestDto) { return this.service.createSupportRequest(user, dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('camera.view')
  @Get('support-requests') listSupportRequests(@CurrentUser() user: CurrentUserDto) { return this.service.listSupportRequests(user); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('system.admin')
  @Post('admin/manufacturers') createManufacturer(@CurrentUser() user: CurrentUserDto, @Body() dto: CreateManufacturerDto) { return this.service.createManufacturer(user, dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('system.admin')
  @Post('admin/models') createModel(@CurrentUser() user: CurrentUserDto, @Body() dto: CreateModelDto) { return this.service.createModel(user, dto); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('system.admin')
  @Post('admin/guides') createGuide(@CurrentUser() user: CurrentUserDto, @Body() dto: CreateGuideDto) { return this.service.createGuide(user, dto); }
}
