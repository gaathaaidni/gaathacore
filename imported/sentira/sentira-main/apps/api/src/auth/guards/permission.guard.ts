import { CanActivate, ExecutionContext, ForbiddenException, Injectable } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Role } from '../../entities';
import { REQUIRE_PERMISSION } from '../decorators/require-permission.decorator';

@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(private reflector: Reflector, @InjectRepository(Role) private roles: Repository<Role>) {}
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const permission = this.reflector.getAllAndOverride<string>(REQUIRE_PERMISSION, [context.getHandler(), context.getClass()]);
    if (!permission) return true;
    const user = context.switchToHttp().getRequest().user;
    if (!user?.id || !user.organizationId || !user.roleId) throw new ForbiddenException('Organization-scoped authentication required');
    const role = await this.roles.findOne({ where: [{ id: user.roleId, organizationId: user.organizationId }, { id: user.roleId, organizationId: null }] });
    if (!role || (!role.permissions?.['system.admin'] && !role.permissions?.[permission])) throw new ForbiddenException(`Missing permission: ${permission}`);
    return true;
  }
}
