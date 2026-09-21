import { MigrationInterface, QueryRunner } from 'typeorm';

export class LegalCompliance1800000013000 implements MigrationInterface {
  name = 'LegalCompliance1800000013000';

  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE TABLE "legal_documents" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "documentType" varchar(64) NOT NULL, "version" varchar(32) NOT NULL, "title" varchar(240) NOT NULL, "content" text NOT NULL, "effectiveAt" TIMESTAMP, "publishedAt" TIMESTAMP, "status" varchar(24) NOT NULL DEFAULT 'DRAFT', "jurisdiction" varchar(64) NOT NULL DEFAULT 'GLOBAL', "language" varchar(16) NOT NULL DEFAULT 'en', "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_legal_documents" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_legal_documents_type_version" ON "legal_documents" ("documentType", "version")`);
    await queryRunner.query(`CREATE INDEX "IDX_legal_documents_publication" ON "legal_documents" ("documentType", "status", "effectiveAt")`);

    await queryRunner.query(`CREATE TABLE "legal_acceptances" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "userId" uuid NOT NULL, "organizationId" uuid NOT NULL, "documentId" uuid NOT NULL, "documentType" varchar(64) NOT NULL, "documentVersion" varchar(32) NOT NULL, "acceptanceType" varchar(24) NOT NULL, "acceptedAt" TIMESTAMP NOT NULL DEFAULT now(), "ipAddress" varchar(128), "userAgent" text, "source" varchar(32) NOT NULL DEFAULT 'WEB', "createdAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_legal_acceptances" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE UNIQUE INDEX "IDX_legal_acceptances_user_document" ON "legal_acceptances" ("userId", "documentType", "documentVersion")`);
    await queryRunner.query(`CREATE INDEX "IDX_legal_acceptances_org_created" ON "legal_acceptances" ("organizationId", "createdAt")`);

    await queryRunner.query(`CREATE TABLE "consent_records" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "consentType" varchar(24) NOT NULL, "userId" uuid, "organizationId" uuid, "subjectHash" varchar(128), "categories" jsonb NOT NULL DEFAULT '{}', "policyVersion" varchar(32), "cookiePolicyVersion" varchar(32), "source" varchar(32) NOT NULL DEFAULT 'WEB', "withdrawnAt" TIMESTAMP, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_consent_records" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_consent_subject_type_created" ON "consent_records" ("subjectHash", "consentType", "createdAt")`);
    await queryRunner.query(`CREATE INDEX "IDX_consent_org_type_created" ON "consent_records" ("organizationId", "consentType", "createdAt")`);

    await queryRunner.query(`CREATE TABLE "privacy_requests" ("id" uuid NOT NULL DEFAULT uuid_generate_v4(), "organizationId" uuid, "requesterUserId" uuid, "requesterEmail" varchar(255) NOT NULL, "requestType" varchar(32) NOT NULL, "description" text, "status" varchar(32) NOT NULL DEFAULT 'SUBMITTED', "identityVerifiedAt" TIMESTAMP, "resolution" text, "completedAt" TIMESTAMP, "createdAt" TIMESTAMP NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP NOT NULL DEFAULT now(), CONSTRAINT "PK_privacy_requests" PRIMARY KEY ("id"))`);
    await queryRunner.query(`CREATE INDEX "IDX_privacy_requests_org_status_created" ON "privacy_requests" ("organizationId", "status", "createdAt")`);

    await queryRunner.query(`ALTER TABLE "legal_acceptances" ADD CONSTRAINT "FK_legal_acceptances_user" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "legal_acceptances" ADD CONSTRAINT "FK_legal_acceptances_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE`);
    await queryRunner.query(`ALTER TABLE "legal_acceptances" ADD CONSTRAINT "FK_legal_acceptances_document" FOREIGN KEY ("documentId") REFERENCES "legal_documents"("id") ON DELETE RESTRICT`);
    await queryRunner.query(`ALTER TABLE "consent_records" ADD CONSTRAINT "FK_consent_user" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "consent_records" ADD CONSTRAINT "FK_consent_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "privacy_requests" ADD CONSTRAINT "FK_privacy_requests_org" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE SET NULL`);
    await queryRunner.query(`ALTER TABLE "privacy_requests" ADD CONSTRAINT "FK_privacy_requests_user" FOREIGN KEY ("requesterUserId") REFERENCES "users"("id") ON DELETE SET NULL`);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP TABLE IF EXISTS "privacy_requests" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "consent_records" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "legal_acceptances" CASCADE`);
    await queryRunner.query(`DROP TABLE IF EXISTS "legal_documents" CASCADE`);
  }
}
