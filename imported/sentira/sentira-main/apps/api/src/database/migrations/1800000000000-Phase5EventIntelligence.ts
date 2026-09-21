import { MigrationInterface, QueryRunner } from 'typeorm';

export class Phase5EventIntelligence1800000000000 implements MigrationInterface {
  name = 'Phase5EventIntelligence1800000000000';
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "firstDetectedAt" TIMESTAMP WITH TIME ZONE`);
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "lastDetectedAt" TIMESTAMP WITH TIME ZONE`);
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "trackId" character varying(128)`);
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "ruleVersion" integer NOT NULL DEFAULT 1`);
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "model" character varying(128)`);
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "modelVersion" character varying(128)`);
    await queryRunner.query(`ALTER TABLE "events" ADD IF NOT EXISTS "evidenceStatus" character varying(50) NOT NULL DEFAULT 'pending'`);
    await queryRunner.query(`ALTER TABLE "organizations" ADD IF NOT EXISTS "retentionDays" integer NOT NULL DEFAULT 30`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS "IDX_events_dedup_phase5" ON "events" ("organizationId", "cameraId", "ruleId", "trackId", "status")`);
  }
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS "IDX_events_dedup_phase5"`);
    await queryRunner.query(`ALTER TABLE "organizations" DROP COLUMN IF EXISTS "retentionDays"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "evidenceStatus"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "modelVersion"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "model"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "ruleVersion"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "trackId"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "lastDetectedAt"`);
    await queryRunner.query(`ALTER TABLE "events" DROP COLUMN IF EXISTS "firstDetectedAt"`);
  }
}
