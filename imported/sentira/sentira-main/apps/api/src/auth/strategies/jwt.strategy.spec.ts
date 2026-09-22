import { UnauthorizedException } from '@nestjs/common';
import { JwtStrategy } from './jwt.strategy';

process.env.JWT_SECRET = 'a-test-secret-that-is-long-enough-for-jwt';

describe('JwtStrategy', () => {
  it('rejects an inactive user even when the access token is otherwise valid', async () => {
    const users = { findOneBy: jest.fn().mockResolvedValue({ id: 'user-1', status: 'inactive' }) } as any;
    const strategy = new JwtStrategy(users);

    await expect(strategy.validate({ sub: 'user-1' })).rejects.toBeInstanceOf(UnauthorizedException);
  });

  it('builds the request identity from the current user record', async () => {
    const users = { findOneBy: jest.fn().mockResolvedValue({ id: 'user-1', email: 'current@example.com', organizationId: 'org-1', roleId: 'role-2', status: 'active' }) } as any;
    const strategy = new JwtStrategy(users);

    await expect(strategy.validate({ sub: 'user-1', email: 'stale@example.com', organizationId: 'wrong-org', roleId: 'old-role' })).resolves.toEqual({
      id: 'user-1',
      email: 'current@example.com',
      organizationId: 'org-1',
      roleId: 'role-2',
    });
  });
});