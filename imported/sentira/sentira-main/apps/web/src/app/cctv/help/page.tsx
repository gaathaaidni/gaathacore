'use client';

import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, Search } from 'lucide-react';
import { useRouter } from 'next/navigation';

const API = process.env.NEXT_PUBLIC_API_URL || '/api';
type Result = { manufacturers: Array<{ id: string; name: string; description?: string }>; models: Array<{ id: string; name: string; modelNumber: string; description?: string }>; guides: Array<{ id: string; title: string; description: string; verificationStatus: string }> };

export default function CctvHelpPage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Result>({ manufacturers: [], models: [], guides: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('sentiraAccount');
    if (!saved) { router.replace('/login'); return; }
    setToken(JSON.parse(saved).accessToken);
  }, [router]);

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setError('');
    try {
      const response = await fetch(`${API}/cctv/help/search?q=${encodeURIComponent(query)}`, { headers: { Authorization: `Bearer ${token}` } });
      const body = await response.json();
      if (!response.ok) throw new Error(body.message || 'Search failed');
      setResults(body);
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Search failed'); }
  }

  return <main className="shell">
    <header className="topbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
      <div><p className="eyebrow">Sentira support</p><h1 style={{ margin: '8px 0 0' }}>CCTV Help Center</h1></div>
      <button type="button" className="button ghost" onClick={() => router.push('/dashboard')}><ArrowLeft size={16} /> Dashboard</button>
    </header>
    <section className="panel" style={{ maxWidth: 900, margin: '0 auto' }}>
      <div className="auth-form"><h2>What do you need help with?</h2><p className="muted">Search by manufacturer, model, DVR, NVR, network, or connection problem.</p><form onSubmit={search} style={{ display: 'flex', gap: 10 }}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="e.g. CP PLUS camera" /><button type="submit" className="button"><Search size={16} /> Search</button></form>{error && <p className="auth-message error">{error}</p>}</div>
      {(results.manufacturers.length > 0 || results.models.length > 0 || results.guides.length > 0) && <div className="grid">
        {results.manufacturers.map((item) => <article className="card" key={item.id}><small>Manufacturer</small><h3>{item.name}</h3><p className="muted">{item.description}</p></article>)}
        {results.models.map((item) => <article className="card" key={item.id}><small>Model</small><h3>{item.name}</h3><p className="muted">{item.modelNumber} {item.description ? `· ${item.description}` : ''}</p></article>)}
        {results.guides.map((item) => <article className="card" key={item.id}><small>Setup guide · {item.verificationStatus}</small><h3>{item.title}</h3><p className="muted">{item.description}</p></article>)}
      </div>}
    </section>
  </main>;
}
