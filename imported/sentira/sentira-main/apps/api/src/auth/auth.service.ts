import { ConflictException, Injectable, UnauthorizedException } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import { IsNull, Repository } from 'typeorm';
import { createHash, randomUUID } from 'crypto';
import { LegalAcceptance, LegalDocument, Organization, Role, User, UserSession } from '../entities';
import { DataSource, QueryFailedError } from 'typeorm';
import { LoginResponseDto } from './auth.dto';
import { FREE_CAMERA_LIMIT, FREE_PLAN } from '../common/entitlements';

@Injectable()
export class AuthService {
  constructor(private jwt?: JwtService, @InjectRepository(User) private users?: Repository<User>, @InjectRepository(UserSession) private sessions?: Repository<UserSession>, @InjectRepository(Organization) private organizations?: Repository<Organization>, @InjectRepository(Role) private roles?: Repository<Role>, private dataSource?: DataSource, @InjectRepository(LegalDocument) private legalDocuments?: Repository<LegalDocument>) {}
  async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, 10);
  }

  async validatePassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }
  private hashRefreshToken(token: string): string {
    return createHash('sha256').update(token, 'utf8').digest('hex');
  }
  private payload(user: User) { return { sub: user.id, email: user.email, organizationId: user.organizationId, roleId: user.roleId }; }
  private async issue(user: User, metadata: { ip?: string; userAgent?: string } = {}, sessions = this.sessions!) {
    const accessToken = await this.jwt!.signAsync(this.payload(user), { expiresIn: (process.env.JWT_ACCESS_TTL || '15m') as any });
    // `jti` makes each rotation unique even when requests occur in the same
    // second (JWT's default `iat` precision), preserving one-time use.
    const raw = await this.jwt!.signAsync({ ...this.payload(user), typ: 'refresh', jti: randomUUID() }, { expiresIn: (process.env.JWT_REFRESH_TTL || '7d') as any });
    const decoded = this.jwt.decode(raw) as { exp?: number };
    await sessions.save({ userId: user.id, refreshTokenHash: this.hashRefreshToken(raw), expiresAt: new Date((decoded.exp ?? 0) * 1000), ipAddress: metadata.ip, userAgent: metadata.userAgent });
    return { accessToken, refreshToken: raw, user: { id: user.id, email: user.email, firstName: user.firstName, lastName: user.lastName, organizationId: user.organizationId } };
  }
  async login(email: string, password: string, metadata?: { ip?: string; userAgent?: string }) {
    const user = await this.users!.findOne({ where: { email }, relations: ['role'] });
    if (!user || user.status !== 'active' || !(await this.validatePassword(password, user.passwordHash))) throw new UnauthorizedException('Invalid credentials');
    user.lastLoginAt = new Date(); await this.users!.save(user); return this.issue(user, metadata);
  }
  async signup(input: { email: string; password: string; organizationName: string; termsAccepted: boolean; privacyAcknowledged: boolean; termsDocumentId: string; privacyDocumentId: string }, metadata?: { ip?: string; userAgent?: string }) {
    if (!this.dataSource) throw new Error('Signup persistence is unavailable');
    if (!input.termsAccepted || !input.privacyAcknowledged) throw new ConflictException('Terms of Service and Privacy Policy acknowledgement are required');
    if (!this.legalDocuments) throw new Error('Legal document persistence is unavailable');
    const legalDocuments = await this.legalDocuments.find({ where: [{ id: input.termsDocumentId, documentType: 'TERMS_OF_SERVICE', status: 'PUBLISHED' }, { id: input.privacyDocumentId, documentType: 'PRIVACY_POLICY', status: 'PUBLISHED' }] });
    const terms = legalDocuments.find((document) => document.id === input.termsDocumentId && document.documentType === 'TERMS_OF_SERVICE');
    const privacy = legalDocuments.find((document) => document.id === input.privacyDocumentId && document.documentType === 'PRIVACY_POLICY');
    if (!terms || !privacy) throw new ConflictException('Current published legal documents are required');
    const email = input.email.trim().toLowerCase();
    const organizationName = input.organizationName.trim();
    try {
      let response: LoginResponseDto;
      await this.dataSource.transaction(async (manager) => {
        const organization = await manager.getRepository(Organization).save({ name: organizationName, plan: FREE_PLAN, cameraLimit: FREE_CAMERA_LIMIT });
        const role = await manager.getRepository(Role).save({ organizationId: organization.id, name: 'Owner', permissions: { 'system.admin': true } });
        const user = await manager.getRepository(User).save({ organizationId: organization.id, email, passwordHash: await this.hashPassword(input.password), roleId: role.id, status: 'active' });
        await manager.getRepository(LegalAcceptance).save([
          { userId: user.id, organizationId: organization.id, documentId: terms.id, documentType: terms.documentType, documentVersion: terms.version, acceptanceType: 'AGREEMENT', source: 'WEB' },
          { userId: user.id, organizationId: organization.id, documentId: privacy.id, documentType: privacy.documentType, documentVersion: privacy.version, acceptanceType: 'ACKNOWLEDGEMENT', source: 'WEB' },
        ]);
        response = await this.issue(user, metadata, manager.getRepository(UserSession));
      });
      return response!;
    } catch (error) {
      if (error instanceof QueryFailedError && (error as any).driverError?.code === '23505') throw new ConflictException('Email is already registered');
      throw error;
    }
  }
  async refresh(raw: string, metadata?: { ip?: string; userAgent?: string }) {
    let payload: any; try { payload = await this.jwt!.verifyAsync(raw); } catch { throw new UnauthorizedException('Invalid refresh token'); }
    if (payload.typ !== 'refresh') throw new UnauthorizedException('Invalid refresh token');
    const candidates = await this.sessions!.find({ where: { userId: payload.sub, revokedAt: IsNull() } });
    const tokenHash = this.hashRefreshToken(raw);
    const session = candidates.find((item) => item.expiresAt > new Date() && item.refreshTokenHash === tokenHash) ?? null;
    if (!session) {
      // A matching revoked token is a replay attempt. Invalidate the user's
      // remaining sessions so a stolen rotated token cannot keep a session alive.
      const previous = await this.sessions!.find({ where: { userId: payload.sub } });
      if (previous.some((item) => item.revokedAt && item.refreshTokenHash === tokenHash)) {
        await this.sessions!.update({ userId: payload.sub, revokedAt: IsNull() }, { revokedAt: new Date() });
      }
      throw new UnauthorizedException('Refresh token revoked');
    }
    // Conditional update is the rotation lock: concurrent requests can both
    // validate a token, but only one can revoke its still-active session.
    const revoked = await this.sessions!.update({ id: session.id, revokedAt: IsNull() }, { revokedAt: new Date() });
    if (revoked.affected !== 1) throw new UnauthorizedException('Refresh token revoked');
    const user = await this.users!.findOneBy({ id: payload.sub }); if (!user || user.status !== 'active') throw new UnauthorizedException('Session user unavailable');
    return this.issue(user, metadata);
  }
  async logout(userId: string, raw?: string) { const sessions = await this.sessions!.find({ where: { userId, revokedAt: IsNull() } }); const tokenHash = raw ? this.hashRefreshToken(raw) : undefined; for (const session of sessions) if (!tokenHash || session.refreshTokenHash === tokenHash) await this.sessions!.update({ id: session.id, revokedAt: IsNull() }, { revokedAt: new Date() }); }
  listSessions(userId: string) { return this.sessions!.find({ where: { userId }, select: ['id', 'createdAt', 'expiresAt', 'revokedAt', 'ipAddress', 'userAgent'], order: { createdAt: 'DESC' } }); }
  async revokeSession(userId: string, id: string) { const session = await this.sessions!.findOneBy({ id, userId }); if (!session) throw new UnauthorizedException('Session not found'); session.revokedAt = new Date(); await this.sessions!.save(session); }
}
