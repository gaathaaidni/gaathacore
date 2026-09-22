import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from '../../entities/user.entity';
import { Role } from '../../entities/role.entity';
import { UsersService } from './users.service';
import { UsersController } from './users.controller';
import { PermissionGuard } from '../../auth/guards/permission.guard';

@Module({
  imports: [TypeOrmModule.forFeature([User, Role])],
  providers: [UsersService, PermissionGuard],
  controllers: [UsersController],
  exports: [UsersService],
})
export class UsersModule {}