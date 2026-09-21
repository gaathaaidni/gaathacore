import Link from 'next/link';

export default function UserPolicyPage() {
  return <main className="legal-page"><header className="legal-header"><Link href="/" className="brand">Sentira AI</Link></header><article className="legal-document"><p className="eyebrow">User Policy</p><h1>Responsible use of visual intelligence.</h1><p className="legal-meta">Last Updated: September 21, 2026</p><div className="legal-copy"><p>Keep accounts, camera credentials, connector tokens, and evidence access secure. Use only the permissions assigned to you and handle people&apos;s information carefully.</p><p>Do not use Sentira for unlawful surveillance, unauthorized access, harassment, discrimination, credential misuse, destructive testing, or attempts to bypass tenant and permission boundaries.</p><p>Report suspected security, privacy, or data-integrity issues through your organization administrator. Access may be restricted when misuse or a security risk is identified.</p></div></article></main>;
}
