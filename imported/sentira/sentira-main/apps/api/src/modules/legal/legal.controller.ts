import { Body, Controller, Get, Param, Patch, Post, Query, Req, UseGuards } from '@nestjs/common';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { RequirePermission } from '../../auth/decorators/require-permission.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { PermissionGuard } from '../../auth/guards/permission.guard';
import { AcceptLegalDocumentDto, CookieConsentDto, CreateLegalDocumentDto, MarketingConsentDto, PrivacyRequestDto, PublishLegalDocumentDto, UpdatePrivacyRequestDto } from './legal.dto';
import { LegalService } from './legal.service';

@Controller('api/legal')
export class LegalController {
  constructor(private readonly legal: LegalService) {}

  @Get('documents')
  listDocuments(@Query('documentType') documentType?: string) { return this.legal.listPublished(documentType); }

  @Get('documents/:documentType')
  getDocument(@Param('documentType') documentType: string) { return this.legal.getPublished(documentType); }

  @UseGuards(JwtAuthGuard)
  @Get('me/acceptances')
  listAcceptances(@CurrentUser() user: CurrentUserDto) { return this.legal.listAcceptances(user); }

  @UseGuards(JwtAuthGuard)
  @Post('acceptances')
  accept(@CurrentUser() user: CurrentUserDto, @Body() dto: AcceptLegalDocumentDto, @Req() request: any) {
    return this.legal.accept(user, dto, { ip: request.ip, userAgent: request.headers['user-agent'] });
  }

  @Post('cookie-consent')
  recordCookieConsent(@Body() dto: CookieConsentDto, @Req() request: any) { return this.legal.recordCookieConsent(dto, { ip: request.ip }); }

  @UseGuards(JwtAuthGuard)
  @Post('marketing-consent')
  recordMarketingConsent(@CurrentUser() user: CurrentUserDto, @Body() dto: MarketingConsentDto) { return this.legal.recordMarketingConsent(user, dto); }

  @UseGuards(JwtAuthGuard)
  @Post('privacy-requests')
  createPrivacyRequest(@CurrentUser() user: CurrentUserDto | undefined, @Body() dto: PrivacyRequestDto) { return this.legal.createPrivacyRequest(user, dto); }

  @UseGuards(JwtAuthGuard)
  @Post('account-deletion')
  requestAccountDeletion(@CurrentUser() user: CurrentUserDto, @Body() dto: PrivacyRequestDto) { return this.legal.createPrivacyRequest(user, { ...dto, requestType: 'ERASURE' }); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('legal:read')
  @Get('admin/documents')
  listAllDocuments() { return this.legal.listAllDocuments(); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('legal:write')
  @Post('admin/documents')
  createDocument(@Body() dto: CreateLegalDocumentDto, @CurrentUser() user: CurrentUserDto) { return this.legal.createDocument(dto, user); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('legal:write')
  @Patch('admin/documents/:id')
  publishDocument(@Param('id') id: string, @Body() dto: PublishLegalDocumentDto, @CurrentUser() user: CurrentUserDto) { return this.legal.publishDocument(id, dto, user); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('legal:read')
  @Get('admin/privacy-requests')
  listPrivacyRequests(@CurrentUser() user: CurrentUserDto) { return this.legal.listPrivacyRequests(user); }

  @UseGuards(JwtAuthGuard, PermissionGuard)
  @RequirePermission('legal:write')
  @Patch('admin/privacy-requests/:id')
  updatePrivacyRequest(@Param('id') id: string, @CurrentUser() user: CurrentUserDto, @Body() dto: UpdatePrivacyRequestDto) { return this.legal.updatePrivacyRequest(id, user, dto); }
}
