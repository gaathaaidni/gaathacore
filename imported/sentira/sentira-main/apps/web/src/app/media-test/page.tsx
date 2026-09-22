'use client';

import { useState } from 'react';

const hlsBaseUrl = process.env.NEXT_PUBLIC_MEDIAMTX_HLS_URL || 'http://localhost:8888';
const paths = {
  a: 'sentira/org-a/site-a/camera-a',
  b: 'sentira/org-b/site-b/camera-b',
};

export default function MediaTestPage() {
  const [tokens, setTokens] = useState({ a: '', b: '' });
  const [results, setResults] = useState({ a: 'No request made', b: 'No request made' });

  const requestMedia = async (tenant: 'a' | 'b') => {
    const response = await fetch(`${hlsBaseUrl}/${paths[tenant]}/index.m3u8`, {
      headers: tokens[tenant] ? { Authorization: `Bearer ${tokens[tenant]}` } : {},
    });
    setResults((current) => ({ ...current, [tenant]: `HLS parent response: ${response.status}` }));
  };

  return (
    <main className="shell">
      <section className="panel" style={{ maxWidth: 900, margin: '0 auto' }}>
        <div>
          <p className="eyebrow">Local Sentira media test</p>
          <h1>Tenant media authorization</h1>
          <p className="muted">Enter a short-lived playback token to test the real MediaMTX callback.</p>
          {(['a', 'b'] as const).map((tenant) => (
            <div key={tenant} style={{ display: 'grid', gap: 8, marginTop: 20 }}>
              <strong>Organization {tenant.toUpperCase()}</strong>
              <code>{paths[tenant]}</code>
              <input
                aria-label={`Organization ${tenant.toUpperCase()} playback token`}
                type="password"
                placeholder="Bearer token"
                value={tokens[tenant]}
                onChange={(event) => setTokens((current) => ({ ...current, [tenant]: event.target.value }))}
              />
              <button type="button" onClick={() => requestMedia(tenant)}>Request HLS parent</button>
              <p className="muted">{results[tenant]}</p>
            </div>
          ))}
          <p className="muted">A browser video element cannot attach an Authorization header without an HLS player library. The request results above prove the authorized or rejected MediaMTX response.</p>
        </div>
      </section>
    </main>
  );
}