import { MigrationInterface, QueryRunner } from 'typeorm';

export class Phase11Entitlements1800000005000 implements MigrationInterface {
  name = 'Phase11Entitlements1800000005000';

  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "organizations" ADD COLUMN IF NOT EXISTS "plan" varchar(32) NOT NULL DEFAULT 'FREE'`);
    await queryRunner.query(`ALTER TABLE "organizations" ADD COLUMN IF NOT EXISTS "cameraLimit" integer NOT NULL DEFAULT 3`);
    await queryRunner.query(`ALTER TABLE "organizations" ADD CONSTRAINT "CHK_organizations_camera_limit_positive" CHECK ("cameraLimit" >= 0)`);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "organizations" DROP CONSTRAINT IF EXISTS "CHK_organizations_camera_limit_positive"`);
    await queryRunner.query(`ALTER TABLE "organizations" DROP COLUMN IF EXISTS "cameraLimit"`);
    await queryRunner.query(`ALTER TABLE "organizations" DROP COLUMN IF EXISTS "plan"`);
  }
}