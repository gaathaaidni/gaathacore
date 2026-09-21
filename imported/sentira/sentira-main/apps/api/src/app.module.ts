import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule } from '@nestjs/config';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import {
  Organization,
  User,
  Role,
  AuditLog,
  Camera,
  Site,
  Zone,
  Rule,
  RuleCondition,
  RuleAction,
  Event,
  EventMedia,
  Notification,
  UserSession,
  Connector,
  DiscoveredCamera,
  CameraOnboardingSession,
  CctvManufacturer,
  CctvModel,
  CctvSetupGuide,
  CctvSetupSession,
  CctvSupportRequest,
  CctvRecorder,
  CctvRecorderChannel,
  CctvConnectionTest,
  LegalDocument,
  LegalAcceptance,
  ConsentRecord,
  PrivacyRequest,
} from './entities';
import { AuthService } from './auth/auth.service';
import { AuthController } from './auth/auth.controller';
import { JwtStrategy } from './auth/strategies/jwt.strategy';
import { UsersModule } from './modules/users/users.module';
import { OrganizationsModule } from './modules/organizations/organizations.module';
import { CamerasModule } from './modules/cameras/cameras.module';
import { EventsModule } from './modules/events/events.module';
import { RulesModule } from './modules/rules/rules.module';
import { ZonesModule } from './modules/zones/zones.module';
import { CommonModule } from './modules/common/common.module';
import { EventGeneratorService } from './services/event-generator.service';
import { RuleEngineService } from './services/rule-engine.service';
import { NotificationService } from './services/notification.service';
import { NotificationQueueService } from './services/notification-queue.service';
import { EventDeduplicationService } from './services/event-deduplication.service';
import { RuleStateService } from './services/rule-state.service';
import { EvidenceService } from './services/evidence.service';
import { HealthService } from './services/health.service';
import { Phase7EnterpriseService } from './services/phase7-enterprise.service';
import { ActionExecutorService } from './services/actions/action-executor.service';
import { RedisStateClient } from './services/redis-state.client';
import { ObjectStorageService } from './services/object-storage.service';
import { MediaRetentionService } from './services/media-retention.service';
import { DetectionProcessorService } from './services/detection-processor.service';
import { DetectionConsumerService } from './services/detection-consumer.service';
import { DemoController } from './controllers/demo.controller';
import { AppController } from './app.controller';
import { DashboardModule } from './modules/dashboard/dashboard.module';
import { EventsGateway } from './events.gateway';
import { databaseConfig } from './config/database.config';
import { AppService } from './app.service';
import { OperationsModule } from './modules/operations/operations.module';
import { CctvModule } from './modules/cctv/cctv.module';
import { LegalModule } from './modules/legal/legal.module';
import { getJwtSecret } from './config/jwt-secret';

const jwtSecret = getJwtSecret();

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      // npm workspace scripts run from apps/api, while local setup is documented at the repo root.
      envFilePath: ['.env.local', '../../.env.local'],
    }),
    UsersModule,
    OrganizationsModule,
    CamerasModule,
    EventsModule,
    RulesModule,
    ZonesModule,
    CommonModule,
    DashboardModule,
    OperationsModule,
    CctvModule,
    LegalModule,
    TypeOrmModule.forRoot(databaseConfig()),
    TypeOrmModule.forFeature([
      Organization,
      User,
      Role,
      AuditLog,
      Camera,
      Site,
      Zone,
      Rule,
      RuleCondition,
      RuleAction,
      Event,
      EventMedia,
      Notification,
      UserSession,
      CctvManufacturer,
      CctvModel,
      CctvSetupGuide,
      CctvSetupSession,
      CctvSupportRequest,
      CctvRecorder,
      CctvRecorderChannel,
      CctvConnectionTest,
      LegalDocument,
      LegalAcceptance,
      ConsentRecord,
      PrivacyRequest,
    ]),
    PassportModule.register({ defaultStrategy: 'jwt' }),
    JwtModule.register({
      secret: jwtSecret,
      signOptions: { expiresIn: '24h' },
    }),
  ],
  controllers: [
    AppController,
    AuthController,
    DemoController,
  ],
  providers: [
    AppService,
    AuthService,
    EventsGateway,
    JwtStrategy,
    EventGeneratorService,
    RuleEngineService,
    NotificationService,
    NotificationQueueService,
    EventDeduplicationService,
    RuleStateService,
    EvidenceService,
    HealthService,
    Phase7EnterpriseService,
    ActionExecutorService,
    RedisStateClient,
    ObjectStorageService,
    MediaRetentionService,
    DetectionProcessorService,
    DetectionConsumerService,
  ],
  exports: [EventsGateway],
})
export class AppModule {}
