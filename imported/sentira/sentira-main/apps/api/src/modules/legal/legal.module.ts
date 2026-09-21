import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuditLog, ConsentRecord, LegalAcceptance, LegalDocument, Organization, PrivacyRequest, Role } from '../../entities';
import { LegalController } from './legal.controller';
import { LegalService } from './legal.service';
import { PermissionGuard } from '../../auth/guards/permission.guard';

@Module({
  imports: [TypeOrmModule.forFeature([AuditLog, ConsentRecord, LegalAcceptance, LegalDocument, Organization, PrivacyRequest, Role])],
  controllers: [LegalController],
  providers: [LegalService, PermissionGuard],
  exports: [LegalService],
})
export class LegalModule {}
