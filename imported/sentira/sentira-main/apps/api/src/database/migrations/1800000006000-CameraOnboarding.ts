import { MigrationInterface, QueryRunner } from 'typeorm';

export class CameraOnboarding1800000006000 implements MigrationInterface {
  name = 'CameraOnboarding1800000006000';

  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "cameras" ALTER COLUMN "streamUrl" DROP NOT NULL`);
    await queryRunner.query(`ALTER TABLE "cameras" ADD COLUMN IF NOT EXISTS "sourceType" varchar(32) NOT NULL DEFAULT 'manual'`);
    await queryRunner.query(`ALTER TABLE "cameras" ADD COLUMN IF NOT EXISTS "connectorId" uuid`);
    await queryRunner.query(`ALTER TABLE "cameras" ADD COLUMN IF NOT EXISTS "discoveredCameraId" uuid`);
    await queryRunner.query(`CREATE TABLE "connectors" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "name" varchar(255) NOT NULL, "status" varchar(32) NOT NULL DEFAULT 'pending', "registrationTokenHash" text, "lastHeartbeatAt" TIMESTAMP, "version" varchar(64), "capabilities" jsonb, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_connectors" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_connectors_org_status" ON "connectors" ("organizationId", "status")`);
    await queryRunner.query(`CREATE TABLE "camera_onboarding_sessions" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "userId" uuid NOT NULL, "method" varchar(32) NOT NULL, "status" varchar(32) NOT NULL DEFAULT 'waiting_for_connector', "pairingCodeHash" text, "expiresAt" TIMESTAMP NOT NULL, "usedAt" TIMESTAMP, "connectorId" uuid, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_camera_onboarding_sessions" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_onboarding_pairing_hash" ON "camera_onboarding_sessions" ("pairingCodeHash")`);
    await queryRunner.query(`CREATE INDEX "IDX_onboarding_org_status" ON "camera_onboarding_sessions" ("organizationId", "status")`);
    await queryRunner.query(`CREATE TABLE "discovered_cameras" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "connectorId" uuid NOT NULL, "name" varchar(255) NOT NULL, "localAddress" varchar(255), "manufacturer" varchar(100), "model" varchar(100), "protocol" varchar(50), "capabilities" jsonb, "discoveryStatus" varchar(32) NOT NULL DEFAULT 'ready', "discoveredAt" TIMESTAMP NOT NULL, "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_discovered_cameras" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_discovered_org_connector_status" ON "discovered_cameras" ("organizationId", "connectorId", "discoveryStatus")`);
    await queryRunner.query(`ALTER TABLE "connectors" ADD CONSTRAINT "FK_connectors_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "camera_onboarding_sessions" ADD CONSTRAINT "FK_onboarding_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "discovered_cameras" ADD CONSTRAINT "FK_discovered_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "discovered_cameras" ADD CONSTRAINT "FK_discovered_connector" FOREIGN KEY ("connectorId") REFERENCES "connectors"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cameras" ADD CONSTRAINT "FK_cameras_connector" FOREIGN KEY ("connectorId") REFERENCES "connectors"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "cameras" ADD CONSTRAINT "FK_cameras_discovered" FOREIGN KEY ("discoveredCameraId") REFERENCES "discovered_cameras"("id") ON DELETE SET NULL`);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP TABLE IF EXISTS "discovered_cameras" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "camera_onboarding_sessions" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "connectors" CASCADE`);
    await queryRunner.query(`ALTER TABLE "cameras" DROP COLUMN IF EXISTS "discoveredCameraId"`);
    await queryRunner.query(`ALTER TABLE "cameras" DROP COLUMN IF EXISTS "connectorId"`);
    await queryRunner.query(`ALTER TABLE "cameras" DROP COLUMN IF EXISTS "sourceType"`);
    await queryRunner.query(`ALTER TABLE "cameras" ALTER COLUMN "streamUrl" SET NOT NULL`);
  }
}
