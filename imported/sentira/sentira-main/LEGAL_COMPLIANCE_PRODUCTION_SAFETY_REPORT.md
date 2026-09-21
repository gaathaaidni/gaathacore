# Legal Compliance Production-Safety Report

Date: 2026-09-09

## Scope

Reviewed the legal framework introduced by commit `81c3d9e`. The existing legal migration was not modified or removed. No production environment files were changed, no database-destructive commands were run, and no legal document was published.

## Behavior Changed

- Legal seed records are idempotent and always created as `DRAFT` with no effective or published timestamp. Placeholder text remains confined to unpublished first-draft material.
- Missing environment configuration remains unset instead of being replaced with fake legal details.
- Publication now fails unless the legal configuration and document metadata are complete and the document title/content contain none of the known unresolved placeholder tokens.
- Publication creates `LEGAL_DOCUMENT_PUBLISHED` only for an actual publication; other administrative status changes use a separate audit action.
- The existing `legal:write` / `system.admin` permission guard continues to protect administrative publication, with an explicit regression test for unauthorized users.
- Public document queries continue to return only effective `PUBLISHED` documents.
- Signup now requires acceptance of the current published Terms and acknowledgement of the current published Privacy Policy by exact document ID. Both immutable versioned acceptance records are saved in the signup transaction; missing documents or unchecked acknowledgements fail closed.
- Repeated acceptance of an exact version is idempotent, while a newer version creates a separate acceptance record. Historical acceptance records are not updated.
- Cookie consent remains separate from marketing consent and legal acceptance. Necessary cookies are always represented as necessary; optional categories can be rejected or withdrawn. Marketing consent is not part of the required signup contract.
- Privacy requests remain organization-scoped for authenticated users, and account-deletion requests use the auditable privacy-request path.
- Unpublished legal pages render an unavailable state without fake title, version, or effective-date placeholders.

## Files Changed

- `apps/api/src/auth/auth.dto.ts`
- `apps/api/src/auth/auth.service.ts`
- `apps/api/src/auth/auth.service.spec.ts`
- `apps/api/src/auth/guards/permission.guard.spec.ts`
- `apps/api/src/config/legal.config.ts`
- `apps/api/src/database/seeds/legal-documents.ts`
- `apps/api/src/database/seeds/legal-documents.spec.ts`
- `apps/api/src/modules/legal/legal.service.ts`
- `apps/api/src/modules/legal/legal.service.spec.ts`
- `apps/web/src/app/legal/[slug]/page.tsx`
- `apps/web/src/app/signup/page.tsx`
- `LEGAL_COMPLIANCE_PRODUCTION_SAFETY_REPORT.md`

The migration `apps/api/src/database/migrations/1800000013000-LegalCompliance.ts` was not changed.

## Verification

Passed:

- `npm run lint --workspace apps/api`
- `npm run lint --workspace apps/web` (existing `<img>` optimization warnings only)
- Focused API tests: 4 suites, 10 tests passed
- `npm run build --workspace apps/api`
- `npm run build --workspace apps/web`
- `git diff --check`

The web build completed successfully and emitted existing image optimization warnings. It also attempted to patch optional lockfile/tooling metadata; those generated changes were removed from the working tree.

## Manual Inputs Still Required

Before any deliberate publication, an authorized administrator and legal reviewer must supply and approve:

- Final Terms of Service, Privacy Policy, Cookie Policy, and any other documents intended for publication.
- Legal entity name and registered address.
- Privacy, DPO, legal, and support contact details as applicable.
- Company registration details.
- Governing law and jurisdiction.
- Confirmed effective date and last-updated metadata in the final document text.
- Final language, jurisdiction, retention, transfer, subprocessor, DPA, surveillance, and security content appropriate to the actual service and jurisdictions.
- A deliberate publication decision for each exact document version.

Required configuration keys are `LEGAL_ENTITY_NAME`, `LEGAL_ENTITY_ADDRESS`, `PRIVACY_EMAIL`, `DPO_EMAIL`, `LEGAL_EMAIL`, `SUPPORT_EMAIL`, `GOVERNING_LAW`, `JURISDICTION`, and `COMPANY_REGISTRATION`. Supplying these values alone does not publish a document; final content must also be free of unresolved placeholders and pass the publication checks.
