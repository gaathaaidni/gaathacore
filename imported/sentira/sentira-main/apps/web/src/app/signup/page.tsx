'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);
  const [legalDocuments, setLegalDocuments] = useState<{ id: string; documentType: string }[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('sentiraAccount');
    if (saved) router.replace('/dashboard');
  }, [router]);

  useEffect(() => {
    fetch(`${API}/legal/documents`).then((response) => response.ok ? response.json() : []).then(setLegalDocuments).catch(() => setLegalDocuments([]));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    const termsDocument = legalDocuments.find((document) => document.documentType === 'TERMS_OF_SERVICE');
    const privacyDocument = legalDocuments.find((document) => document.documentType === 'PRIVACY_POLICY');
    if (!termsAccepted || !privacyAcknowledged || !termsDocument || !privacyDocument) {
      setMessage('The current Terms of Service and Privacy Policy must be available and accepted before creating an account.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API}/auth/signup`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email, password, organizationName, termsAccepted, privacyAcknowledged, termsDocumentId: termsDocument.id, privacyDocumentId: privacyDocument.id }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.message || body.error || 'Unable to create account.');
      }
      localStorage.setItem('sentiraAccount', JSON.stringify(body));
      router.push('/dashboard');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to create account.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-head">
          <span className="brand-mark">
            <img src="/logo.png" alt="Sentira AI" width={40} height={40} />
          </span>
          <h1>Get Started</h1>
        </div>

        <div className="auth-tabs">
          <Link href="/login" style={{ display: 'grid', placeItems: 'center', color: '#aac3d9', textDecoration: 'none', borderRadius: 10 }}>Login</Link>
          <button type="button" className="active">Sign Up</button>
        </div>

        <div className="auth-form">
          <label>
            Email
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label>
            Password
            <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          <label>
            Organization name
            <input type="text" required minLength={2} value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} />
          </label>
          <label className="consent-check"><input type="checkbox" required checked={termsAccepted} onChange={(e) => setTermsAccepted(e.target.checked)} /> I agree to the <Link href="/legal/terms" target="_blank">Terms of Service</Link>.</label>
          <label className="consent-check"><input type="checkbox" required checked={privacyAcknowledged} onChange={(e) => setPrivacyAcknowledged(e.target.checked)} /> I acknowledge the <Link href="/legal/privacy" target="_blank">Privacy Policy</Link>.</label>
          {(!legalDocuments.find((document) => document.documentType === 'TERMS_OF_SERVICE') || !legalDocuments.find((document) => document.documentType === 'PRIVACY_POLICY')) && <p className="auth-message">Signup is unavailable until the reviewed legal documents are published.</p>}
          <button type="submit" className="button submit-button" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
          {message && <p className="auth-message error">{message}</p>}
          <p className="auth-message">
            Already have an account? <Link href="/login">Login</Link>
          </p>
          <p className="auth-message">
            <Link href="/">Back to Sentira AI</Link>
          </p>
        </div>
      </form>
    </main>
  );
}
