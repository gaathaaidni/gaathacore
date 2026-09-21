import { MigrationInterface, QueryRunner } from 'typeorm';

export class Phase10CEvidenceIntegrity1800000004000 implements MigrationInterface {
  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS sha256 varchar(64)`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "byteSize" integer`);
    await queryRunner.query(`ALTER TABLE event_media ADD COLUMN IF NOT EXISTS "contentType" varchar(128)`);
    await queryRunner.query(`CREATE INDEX IF NOT EXISTS idx_event_media_org_event ON event_media("organizationId", "eventId")`);
  }
  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX IF EXISTS idx_event_media_org_event`);
    await queryRunner.query(`ALTER TABLE event_media DROP COLUMN IF EXISTS "contentType"`);
    await queryRunner.query(`ALTER TABLE event_media DROP COLUMN IF EXISTS "byteSize"`);
    await queryRunner.query(`ALTER TABLE event_media DROP COLUMN IF EXISTS sha256`);
  }
}
