import { Body, Controller, Delete, Get, Headers, Param, Post, Req, UseGuards } from '@nestjs/common';
import { AuthService } from './auth.service';
import { CurrentUserDto, LoginDto, RefreshDto, SignupDto } from './auth.dto';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { CurrentUser } from './decorators/current-user.decorator';

@Controller('api/auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('signup')
  async signup(@Body() dto: SignupDto, @Req() req: any) { return this.authService.signup(dto, { ip: req.ip, userAgent: req.headers['user-agent'] }); }

  @Post('login')
  async login(@Body() dto: LoginDto, @Req() req: any) { return this.authService.login(dto.email, dto.password, { ip: req.ip, userAgent: req.headers['user-agent'] }); }
  @Post('refresh') async refresh(@Body() dto: RefreshDto, @Req() req: any) { return this.authService.refresh(dto.refreshToken, { ip: req.ip, userAgent: req.headers['user-agent'] }); }
  @Post('logout') @UseGuards(JwtAuthGuard) async logout(@CurrentUser() user: CurrentUserDto, @Body() dto: Partial<RefreshDto>) { await this.authService.logout(user.id, dto.refreshToken); return { ok: true }; }
  @Get('sessions') @UseGuards(JwtAuthGuard) sessions(@CurrentUser() user: CurrentUserDto) { return this.authService.listSessions(user.id); }
  @Delete('sessions/:id') @UseGuards(JwtAuthGuard) async revoke(@CurrentUser() user: CurrentUserDto, @Param('id') id: string) { await this.authService.revokeSession(user.id, id); return { ok: true }; }
}
