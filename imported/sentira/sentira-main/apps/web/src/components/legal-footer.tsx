import Link from 'next/link';

export function LegalFooter() {
  return <footer className="legal-footer"><div className="footer-inner"><span>Sentira by Gaatha Ventures</span><nav aria-label="Legal"><Link href="/legal/terms">Terms</Link><Link href="/legal/privacy">Privacy</Link><Link href="/legal/cookies">Cookies</Link><Link href="/legal/acceptable-use">Acceptable use</Link><Link href="/legal/ai-transparency">AI transparency</Link><Link href="/legal/security">Security</Link><Link href="/legal/subprocessors">Subprocessors</Link></nav></div></footer>;
}
