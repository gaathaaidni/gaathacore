import { MigrationInterface, QueryRunner } from 'typeorm';

export class CctvGuidedOnboarding1800000007000 implements MigrationInterface {
  name = 'CctvGuidedOnboarding1800000007000';

  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE TABLE "cctv_manufacturers" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "name" varchar(120) NOT NULL, "slug" varchar(140) NOT NULL, "description" text, "websiteUrl" varchar(500), "logoUrl" varchar(500), "active" boolean NOT NULL DEFAULT true, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_manufacturers" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_cctv_manufacturer_slug" ON "cctv_manufacturers" ("slug")`);
    await queryRunner.query(`CREATE TABLE "cctv_models" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "manufacturerId" uuid NOT NULL, "modelNumber" varchar(160) NOT NULL, "name" varchar(180) NOT NULL, "slug" varchar(180) NOT NULL, "deviceType" varchar(40) NOT NULL, "description" text, "supportedProtocols" jsonb NOT NULL DEFAULT '[]', "discoveryMethods" jsonb NOT NULL DEFAULT '[]', "active" boolean NOT NULL DEFAULT true, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_models" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_cctv_model_manufacturer_slug" ON "cctv_models" ("manufacturerId", "slug")`);
    await queryRunner.query(`CREATE TABLE "cctv_setup_guides" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "manufacturerId" uuid, "modelId" uuid, "title" varchar(180) NOT NULL, "description" text NOT NULL, "difficulty" varchar(32) NOT NULL DEFAULT 'beginner', "estimatedMinutes" integer NOT NULL DEFAULT 15, "prerequisites" jsonb NOT NULL DEFAULT '[]', "steps" jsonb NOT NULL DEFAULT '[]', "troubleshooting" jsonb NOT NULL DEFAULT '[]', "verificationStatus" varchar(80) NOT NULL DEFAULT 'unverified', "lastVerifiedAt" TIMESTAMP, "version" integer NOT NULL DEFAULT 1, "active" boolean NOT NULL DEFAULT true, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_setup_guides" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_guide_scope" ON "cctv_setup_guides" ("manufacturerId", "modelId", "active")`);
    await queryRunner.query(`CREATE TABLE "cctv_setup_sessions" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "userId" uuid NOT NULL, "siteId" uuid, "deviceType" varchar(40), "manufacturerId" uuid, "modelId" uuid, "guideId" uuid, "connectorId" uuid, "pairingCodeHash" text, "pairingExpiresAt" TIMESTAMP, "pairingUsedAt" TIMESTAMP, "status" varchar(32) NOT NULL DEFAULT 'STARTED', "stage" varchar(32) NOT NULL DEFAULT 'IDENTIFY', "currentStep" varchar(120), "completionPercent" integer NOT NULL DEFAULT 0, "answers" jsonb NOT NULL DEFAULT '{}', "testResult" jsonb, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_setup_sessions" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_setup_org_status" ON "cctv_setup_sessions" ("organizationId", "status")`);
    await queryRunner.query(`CREATE TABLE "cctv_support_requests" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "userId" uuid NOT NULL, "setupSessionId" uuid, "siteId" uuid, "cameraId" uuid, "status" varchar(32) NOT NULL DEFAULT 'OPEN', "priority" varchar(16) NOT NULL DEFAULT 'NORMAL', "reason" varchar(40) NOT NULL, "message" text, "context" jsonb NOT NULL DEFAULT '{}', "assignedTo" uuid, "resolution" text, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_support_requests" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_support_org_status" ON "cctv_support_requests" ("organizationId", "status")`);
    await queryRunner.query(`CREATE TABLE "cctv_connection_tests" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "setupSessionId" uuid NOT NULL, "cameraId" uuid, "connectorType" varchar(40) NOT NULL, "protocol" varchar(20) NOT NULL, "status" varchar(32) NOT NULL, "failureCode" varchar(64), "diagnostics" jsonb NOT NULL DEFAULT '{}', "durationMs" integer, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_connection_tests" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_tests_org_session_created" ON "cctv_connection_tests" ("organizationId", "setupSessionId", "createdAt")`);
    await queryRunner.query(`ALTER TABLE "cctv_models" ADD CONSTRAINT "FK_cctv_models_manufacturer" FOREIGN KEY ("manufacturerId") REFERENCES "cctv_manufacturers"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_setup_guides" ADD CONSTRAINT "FK_cctv_guides_manufacturer" FOREIGN KEY ("manufacturerId") REFERENCES "cctv_manufacturers"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "cctv_setup_guides" ADD CONSTRAINT "FK_cctv_guides_model" FOREIGN KEY ("modelId") REFERENCES "cctv_models"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "cctv_setup_sessions" ADD CONSTRAINT "FK_cctv_sessions_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_setup_sessions" ADD CONSTRAINT "FK_cctv_sessions_connector" FOREIGN KEY ("connectorId") REFERENCES "connectors"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "cctv_support_requests" ADD CONSTRAINT "FK_cctv_support_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`CREATE TABLE "cctv_recorders" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "connectorId" uuid NOT NULL, "setupSessionId" uuid, "name" varchar(255) NOT NULL, "manufacturer" varchar(100), "model" varchar(100), "deviceType" varchar(32) NOT NULL, "status" varchar(32) NOT NULL DEFAULT 'DISCOVERED', "metadata" jsonb NOT NULL DEFAULT '{}', "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_recorders" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_recorders_org_connector" ON "cctv_recorders" ("organizationId", "connectorId")`);
    await queryRunner.query(`CREATE TABLE "cctv_recorder_channels" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "recorderId" uuid NOT NULL, "organizationId" uuid NOT NULL, "channelNumber" integer NOT NULL, "name" varchar(255), "available" boolean NOT NULL DEFAULT false, "protocol" varchar(20), "streamAvailable" boolean NOT NULL DEFAULT false, "verificationStatus" varchar(32) NOT NULL DEFAULT 'UNAVAILABLE', "cameraId" uuid, "metadata" jsonb NOT NULL DEFAULT '{}', "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_recorder_channels" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_cctv_channels_recorder_number" ON "cctv_recorder_channels" ("recorderId", "channelNumber")`);
    await queryRunner.query(`ALTER TABLE "cctv_recorders" ADD CONSTRAINT "FK_cctv_recorders_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_recorders" ADD CONSTRAINT "FK_cctv_recorders_connector" FOREIGN KEY ("connectorId") REFERENCES "connectors"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_recorder_channels" ADD CONSTRAINT "FK_cctv_channels_recorder" FOREIGN KEY ("recorderId") REFERENCES "cctv_recorders"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_recorder_channels" ADD CONSTRAINT "FK_cctv_channels_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_recorder_channels" ADD CONSTRAINT "FK_cctv_channels_camera" FOREIGN KEY ("cameraId") REFERENCES "cameras"("id") ON DELETE SET NULL`);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_recorder_channels" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_recorders" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_connection_tests" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_support_requests" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_setup_sessions" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_setup_guides" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_models" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_manufacturers" CASCADE`);
  }
}
