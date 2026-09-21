export function getJwtSecret(): string {
  const secret = process.env.JWT_SECRET?.trim();

  if (!secret || secret.length < 32) {
    throw new Error('JWT_SECRET must be set to at least 32 characters in every environment');
  }

  return secret;
}
