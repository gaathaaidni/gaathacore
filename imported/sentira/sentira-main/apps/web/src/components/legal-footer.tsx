import Link from 'next/link';

export function LegalFooter() {
  return <footer className="legal-footer"><div className="footer-inner"><span>Sentira AI</span><nav aria-label="Public pages"><Link href="/">Home</Link><Link href="/about">About</Link><Link href="/contact">Contact</Link><Link href="/terms">Terms</Link><Link href="/privacy">Privacy</Link><Link href="/user-policy">User Policy</Link></nav><span>Architect, Developer, Owner, Founder — Hardikkumar Gajjar</span></div></footer>;
}
