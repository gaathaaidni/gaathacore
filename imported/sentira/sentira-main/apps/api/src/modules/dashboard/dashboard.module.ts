import { Module } from '@nestjs/common';
import { OrganizationsModule } from '../organizations/organizations.module';
import { DashboardController } from './dashboard.controller';

@Module({
  imports: [OrganizationsModule],
  controllers: [DashboardController],
})
export class DashboardModule {}
