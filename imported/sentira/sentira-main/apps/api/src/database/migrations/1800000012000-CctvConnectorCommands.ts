import { MigrationInterface, QueryRunner } from 'typeorm';

export class CctvConnectorCommands1800000012000 implements MigrationInterface {
  name = 'CctvConnectorCommands1800000012000';

  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE TABLE "cctv_connector_commands" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid NOT NULL, "connectorId" uuid NOT NULL, "commandType" varchar(40) NOT NULL, "status" varchar(32) NOT NULL DEFAULT 'QUEUED', "payload" jsonb NOT NULL DEFAULT '{}', "result" jsonb NOT NULL DEFAULT '{}', "errorCode" varchar(80), "errorMessage" text, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "queuedAt" TIMESTAMP, "startedAt" TIMESTAMP, "completedAt" TIMESTAMP, "expiresAt" TIMESTAMP, "attemptCount" integer NOT NULL DEFAULT 0, "maxAttempts" integer NOT NULL DEFAULT 1, "correlationId" varchar(64), "idempotencyKey" text, "commandVersion" integer NOT NULL DEFAULT 1, "leaseUntil" TIMESTAMP, "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_cctv_connector_commands" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_commands_org_status_created" ON "cctv_connector_commands" ("organizationId", "status", "createdAt")`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_commands_connector_status_expires" ON "cctv_connector_commands" ("connectorId", "status", "expiresAt")`);
    await queryRunner.query(`CREATE INDEX "IDX_cctv_commands_correlation" ON "cctv_connector_commands" ("correlationId")`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_cctv_commands_idempotency" ON "cctv_connector_commands" ("idempotencyKey") WHERE "idempotencyKey" IS NOT NULL`);
    await queryRunner.query(`ALTER TABLE "cctv_connector_commands" ADD CONSTRAINT "FK_cctv_commands_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "cctv_connector_commands" ADD CONSTRAINT "FK_cctv_commands_connector" FOREIGN KEY ("connectorId") REFERENCES "connectors"("id") ON DELETE CASCADE`);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP TABLE IF EXISTS "cctv_connector_commands" CASCADE`);
  }
}
