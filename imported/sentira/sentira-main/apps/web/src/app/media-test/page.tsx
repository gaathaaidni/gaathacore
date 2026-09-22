'use client';

import { useState } from 'react';

const fixturePath = 'sentira/fixture-org/fixture-site/fixture-camera';
const hlsUrl = `${process.env.NEXT_PUBLIC_MEDIAMTX_HLS_URL || 'http://localhost:8888'}/${fixturePath}/index.m3u8`;

export default function MediaTestPage() {
  const [status, setStatus] = useState('No media request made');

  return (
    <main className="shell">
      <section className="panel" style={{ maxWidth: 900, margin: '0 auto' }}>
        <div>
          <p className="eyebrow">Local Sentira media test</p>
          <h1>Controlled fixture playback</h1>
          <p className="muted">This page targets the disposable MediaMTX fixture. It is not an authorization boundary.</p>
          <video
            controls
            muted
            playsInline
            preload="metadata"
            src={hlsUrl}
            style={{ width: '100%', aspectRatio: '16 / 9', background: '#02070b', borderRadius: 12 }}
            onLoadStart={() => setStatus('HLS request started')}
            onCanPlay={() => setStatus('Browser reported media ready')}
            onError={() => setStatus('Browser could not play this HLS response')}
          />
          <p className="muted">{status}</p>
          <p className="muted">Path: {fixturePath}</p>
        </div>
      </section>
    </main>
  );
}