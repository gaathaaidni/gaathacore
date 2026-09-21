import { AuthService } from './auth.service';
import { JwtService } from '@nestjs/jwt';

describe('AuthService', () => {
  it('should hash a password and validate it', async () => {
    const authService = new AuthService();
    const password = 'StrongPass@123';
    const hash = await authService.hashPassword(password);

    expect(hash).not.toBe(password);
    expect(await authService.validatePassword(password, hash)).toBe(true);
  });

  it('issues unique hashed refresh tokens for successive sessions', async () => {
    const sessions: any[] = [];
    const sessionRepository: any = {
      save: jest.fn(async (session: any) => { session.id ??= `session-${sessions.length + 1}`; sessions.push(session); return session; }),
      find: jest.fn(async (options?: any) => options?.where?.revokedAt ? sessions.filter((session) => !session.revokedAt) : sessions),
      update: jest.fn(async (criteria: any, update: any) => {
        const matching = sessions.filter((session) => (!criteria.id || session.id === criteria.id) && (!criteria.userId || session.userId === criteria.userId) && (criteria.revokedAt === undefined || session.revokedAt === null || session.revokedAt === undefined));
        matching.forEach((session) => Object.assign(session, update));
        return { affected: matching.length };
      }),
    };
    const user: any = { id: 'user-1', email: 'ops@sentira.ai', organizationId: 'org-1', roleId: 'role-1', status: 'active', firstName: 'Ops', lastName: 'User' };
    const users: any = { findOneBy: jest.fn(async () => user) };
    const service = new AuthService(new JwtService({ secret: 'a-test-secret-that-is-long-enough-for-jwt' }), users, sessionRepository);

    const issued = await (service as any).issue(user);
    const next = await (service as any).issue(user);
    expect(next.refreshToken).not.toBe(issued.refreshToken);
    expect(sessions[0].refreshTokenHash).not.toContain(issued.refreshToken);
    expect(sessions[1].refreshTokenHash).not.toContain(next.refreshToken);
  });

  it('creates the organization, owner, user, and initial session in one transaction', async () => {
    const saved: Record<string, any[]> = { organizations: [], roles: [], users: [], user_sessions: [] };
    const repositoryKeys = ['organizations', 'roles', 'users', 'legal_acceptances', 'user_sessions']; let repositoryIndex = 0;
    saved.legal_acceptances = [];
    const manager: any = { getRepository: () => { const key = repositoryKeys[repositoryIndex++]; return { save: jest.fn(async (value: any) => { const values = Array.isArray(value) ? value : [value]; const results = values.map((item) => ({ id: `${key}-id`, ...item })); saved[key].push(...results); return Array.isArray(value) ? results : results[0]; }) }; } };
    const dataSource: any = { transaction: jest.fn(async (callback: any) => callback(manager)) };
    const legalDocuments: any = { find: jest.fn(async () => [
      { id: 'terms-document', documentType: 'TERMS_OF_SERVICE', version: '1.0', status: 'PUBLISHED' },
      { id: 'privacy-document', documentType: 'PRIVACY_POLICY', version: '1.0', status: 'PUBLISHED' },
    ]) };
    const service = new AuthService(new JwtService({ secret: 'a-test-secret-that-is-long-enough-for-jwt' }), undefined, undefined, undefined, undefined, dataSource, legalDocuments);
    const response = await service.signup({ email: 'new@example.com', password: 'strong-password', organizationName: 'New Org', termsAccepted: true, privacyAcknowledged: true, termsDocumentId: 'terms-document', privacyDocumentId: 'privacy-document' });
    expect(dataSource.transaction).toHaveBeenCalledTimes(1);
    expect(saved.organizations[0]).toMatchObject({ name: 'New Org', plan: 'FREE', cameraLimit: 3 });
    expect(saved.roles[0]).toMatchObject({ name: 'Owner', permissions: { 'system.admin': true } });
    expect(saved.users[0]).toMatchObject({ email: 'new@example.com', organizationId: 'organizations-id', roleId: 'roles-id' });
    expect(saved.legal_acceptances).toHaveLength(2);
    expect(response.user.organizationId).toBe('organizations-id');
    expect(saved.user_sessions).toHaveLength(1);
  });
});
