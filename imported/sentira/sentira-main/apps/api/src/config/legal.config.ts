export const legalConfig = () => ({
  entityName: process.env.LEGAL_ENTITY_NAME,
  entityAddress: process.env.LEGAL_ENTITY_ADDRESS,
  privacyEmail: process.env.PRIVACY_EMAIL,
  dpoEmail: process.env.DPO_EMAIL,
  legalEmail: process.env.LEGAL_EMAIL,
  supportEmail: process.env.SUPPORT_EMAIL,
  governingLaw: process.env.GOVERNING_LAW,
  jurisdiction: process.env.JURISDICTION,
  companyRegistration: process.env.COMPANY_REGISTRATION,
});

export type LegalConfig = ReturnType<typeof legalConfig>;

export const REQUIRED_LEGAL_PLACEHOLDERS = [
  '[LEGAL_ENTITY_NAME]', '[REGISTERED_ADDRESS]', '[PRIVACY_EMAIL]', '[DPO_EMAIL]',
  '[LEGAL_EMAIL]', '[SUPPORT_EMAIL]', '[GOVERNING_LAW]', '[JURISDICTION]',
  '[COMPANY_REGISTRATION]', '[EFFECTIVE_DATE]', '[LAST_UPDATED]',
];

export function hasCompleteLegalConfig(config: LegalConfig = legalConfig()): boolean {
  return Object.values(config).every((value) => typeof value === 'string' && value.trim().length > 0);
}
