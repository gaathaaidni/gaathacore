import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { OrganizationsModule } from '../organizations/organizations.module';
import { DashboardController } from './dashboard.controller';
import { Role } from '../../entities/role.entity';
import { PermissionGuard } from '../../auth/guards/permission.guard';

@Module({
  imports: [OrganizationsModule, TypeOrmModule.forFeature([Role])],
  controllers: [DashboardController],
  providers: [PermissionGuard],
})
export class DashboardModule {}
