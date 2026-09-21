'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('sentiraAccount');
    if (saved) router.replace('/dashboard');
  }, [router]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.message || body.error || 'Unable to log in.');
      }
      localStorage.setItem('sentiraAccount', JSON.stringify(body));
      router.push('/dashboard');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to log in.');
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
          <h1>Login</h1>
        </div>

        <div className="auth-tabs">
          <button type="button" className="active">Login</button>
          <Link href="/signup" style={{ display: 'grid', placeItems: 'center', color: '#aac3d9', textDecoration: 'none', borderRadius: 10 }}>Sign Up</Link>
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
          <button type="submit" className="button submit-button" disabled={loading}>
            {loading ? 'Signing in…' : 'Login'}
          </button>
          {message && <p className="auth-message error">{message}</p>}
          <p className="auth-message">
            Need an account? <Link href="/signup">Create one</Link>
          </p>
          <p className="auth-message">
            <Link href="/">Back to Sentira AI</Link>
          </p>
        </div>
      </form>
    </main>
  );
}
