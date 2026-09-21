import Link from 'next/link';

export default function AboutPage() {
  return <main className="legal-page"><header className="legal-header"><Link href="/" className="brand">Sentira AI</Link><Link href="/signup" className="button">Get Started</Link></header><article className="legal-document"><p className="eyebrow">About Sentira AI</p><h1>Visual intelligence for camera-enabled operations.</h1><div className="legal-copy"><p>Sentira connects supported camera feeds with organization-aware monitoring, configured rules, event workflows, notifications, and evidence review.</p><p>It is intended for organizations that need a structured way to review operational signals while keeping people responsible for decisions.</p><p><strong>Architect, Developer, Owner, Founder — Hardikkumar Gajjar</strong></p></div></article></main>;
}
