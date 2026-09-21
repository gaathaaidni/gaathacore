import { MigrationInterface, QueryRunner } from 'typeorm';

export class Phase7EnterpriseOperations1800000002000 implements MigrationInterface {
  name = 'Phase7EnterpriseOperations1800000002000';
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "priority" varchar(50) DEFAULT 'medium'`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "slaDueAt" timestamptz`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "escalatedAt" timestamptz`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "operatorNotes" text`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "investigationNotes" text`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "resolutionReason" varchar(255)`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "falsePositiveReason" varchar(255)`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "eventTimestamp" timestamptz`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "cameraTimestamp" timestamptz`);
    await queryRunner.query(`ALTER TABLE events ADD COLUMN IF NOT EXISTS "detectionTimestamp" timestamptz`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "sha256" varchar(64)`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "fileSizeBytes" bigint`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "frameRate" numeric`);
    await queryRunner.query(`ALTER TABLE cameras ADD COLUMN IF NOT EXISTS "healthScore" integer DEFAULT 0`);
    await queryRunner.query(`ALTER TABLE cameras ADD COLUMN IF NOT EXISTS "lastFrameAt" timestamptz`);
    await queryRunner.query(`ALTER TABLE cameras ADD COLUMN IF NOT EXISTS "streamErrorClass" varchar(100)`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS idx_events_org_severity_created ON events("organizationId", severity, "createdAt")`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS idx_event_media_integrity ON event_media("organizationId", "cameraId", sha256)`);
  }
  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS idx_event_media_integrity`);
    await queryRunner.query(`DROP INDEX IF EXISTS idx_events_org_severity_created`);
  }
}
