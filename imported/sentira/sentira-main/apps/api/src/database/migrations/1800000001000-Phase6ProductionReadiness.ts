import { MigrationInterface, QueryRunner } from 'typeorm';

export class Phase6ProductionReadiness1800000001000 implements MigrationInterface {
  name = 'Phase6ProductionReadiness1800000001000';
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE rules ADD COLUMN IF NOT EXISTS "definitionJson" jsonb`);
    await queryRunner.query(`ALTER TABLE rules ADD COLUMN IF NOT EXISTS "cooldownSeconds" integer NOT NULL DEFAULT 60`);
    await queryRunner.query(`ALTER TABLE rules ADD COLUMN IF NOT EXISTS "duplicateWindowSeconds" integer NOT NULL DEFAULT 10`);
    await queryRunner.query(`ALTER TABLE rules ADD COLUMN IF NOT EXISTS severity varchar(50) NOT NULL DEFAULT 'medium'`);
    await queryRunner.query(`ALTER TABLE rules ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "organizationId" uuid`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "cameraId" uuid`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "storageKey" varchar(500)`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "capturedAt" timestamptz`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "expiresAt" timestamptz`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "metadataJson" jsonb`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS idx_rules_phase6_scope ON rules ("organizationId", "cameraId", "isActive", status)`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS idx_event_media_phase6_scope ON event_media ("organizationId", "cameraId", "eventId")`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS idx_events_phase6_retention ON events ("organizationId", status, "createdAt")`);
  }
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS idx_events_phase6_retention`);
    await queryRunner.query(`DROP INDEX IF EXISTS idx_event_media_phase6_scope`);
    await queryRunner.query(`DROP INDEX IF EXISTS idx_rules_phase6_scope`);
    await queryRunner.query(`ALTER TABLE rules DROP COLUMN IF EXISTS version, DROP COLUMN IF EXISTS severity, DROP COLUMN IF EXISTS "duplicateWindowSeconds", DROP COLUMN IF EXISTS "cooldownSeconds", DROP COLUMN IF EXISTS "definitionJson"`);
    await queryRunner.query(`ALTER TABLE event_media DROP COLUMN IF EXISTS "metadataJson", DROP COLUMN IF EXISTS "expiresAt", DROP COLUMN IF EXISTS "capturedAt", DROP COLUMN IF EXISTS "storageKey", DROP COLUMN IF EXISTS "cameraId", DROP COLUMN IF EXISTS "organizationId"`);
  }
}
