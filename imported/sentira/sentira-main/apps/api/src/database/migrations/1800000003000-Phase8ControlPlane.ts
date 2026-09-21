import { MigrationInterface, QueryRunner } from 'typeorm';
export class Phase8ControlPlane1800000003000 implements MigrationInterface {
  async up(q: QueryRunner): Promise<void> {
    await q.query(`CREATE TABLE IF NOT EXISTS user_sessions (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), "userId" uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE, "refreshTokenHash" varchar(255) NOT NULL, "expiresAt" timestamptz NOT NULL, "revokedAt" timestamptz, "userAgent" varchar(255), "ipAddress" varchar(64), "createdAt" timestamptz NOT NULL DEFAULT now())`);
    await q.query(`CREATE INDEX IF NOT EXISTS idx_sessions_user_revoked ON user_sessions("userId", "revokedAt")`);
    await q.query(`CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON user_sessions("userId", "expiresAt")`);
    for (const sql of [`ALTER TABLE events ADD COLUMN IF NOT EXISTS "acknowledgedAt" timestamptz`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "investigatingAt" timestamptz`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "resolvedAt" timestamptz`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "slaState" varchar(20) DEFAULT 'on_track'`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "slaBreachedAt" timestamptz`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "internalComments" text`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "escalationReason" varchar(255)`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "assignedTeamId" uuid`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "relatedEventIds" uuid[] DEFAULT '{}'`, `ALTER TABLE events ADD COLUMN IF NOT EXISTS "correlationId" varchar(100)`]) await q.query(sql);
    await q.query(`CREATE INDEX IF NOT EXISTS idx_events_org_status_created ON events("organizationId", status, "createdAt")`);
  }
  async down(q: QueryRunner): Promise<void> { await q.query(`DROP INDEX IF EXISTS idx_sessions_user_expires`); await q.query(`DROP TABLE IF EXISTS user_sessions`); await q.query(`DROP INDEX IF EXISTS idx_events_org_status_created`); }
}
