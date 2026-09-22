import { ForbiddenException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { PermissionGuard } from './permission.guard';

describe('PermissionGuard', () => {
  it('rejects a non-administrative user without the required permission', async () => {
    const reflector = { getAllAndOverride: jest.fn(() => 'legal:write') } as unknown as Reflector;
    const roles = { findOne: jest.fn(async () => ({ permissions: { 'legal:read': true } })) } as any;
    const context = {
      getHandler: jest.fn(),
      getClass: jest.fn(),
      switchToHttp: () => ({ getRequest: () => ({ user: { id: 'user-1', organizationId: 'org-1', roleId: 'role-1' } }) }),
    } as any;
    const guard = new PermissionGuard(reflector, roles);

    await expect(guard.canActivate(context)).rejects.toBeInstanceOf(ForbiddenException);
  });

  it('allows a matching global role without organization ownership', async () => {
    const reflector = { getAllAndOverride: jest.fn(() => 'analytics.view') } as unknown as Reflector;
    const roles = { findOne: jest.fn(async () => ({ organizationId: null, permissions: { 'analytics.view': true } })) } as any;
    const context = {
      getHandler: jest.fn(),
      getClass: jest.fn(),
      switchToHttp: () => ({ getRequest: () => ({ user: { id: 'user-1', organizationId: 'org-1', roleId: 'global-role' } }) }),
    } as any;
    const guard = new PermissionGuard(reflector, roles);

    await expect(guard.canActivate(context)).resolves.toBe(true);
  });
});