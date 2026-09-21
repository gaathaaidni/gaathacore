import Link from 'next/link';

export default function ContactPage() {
  return <main className="legal-page"><header className="legal-header"><Link href="/" className="brand">Sentira AI</Link><Link href="/login" className="button secondary">Login</Link></header><article className="legal-document"><p className="eyebrow">Contact</p><h1>Support for your Sentira deployment.</h1><div className="legal-copy"><p>Use the support or administrator channel provided for your organization or deployment.</p><p>No public email address or message-delivery endpoint is configured in this application, so this page does not claim to send a message.</p><p>Administration identity: <strong>Admin — Jaygiri Gosai</strong></p></div></article></main>;
}
