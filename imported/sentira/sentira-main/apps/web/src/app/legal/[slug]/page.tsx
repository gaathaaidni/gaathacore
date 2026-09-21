'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api';
const types: Record<string, string> = {
  terms: 'TERMS_OF_SERVICE', privacy: 'PRIVACY_POLICY', cookies: 'COOKIE_POLICY', 'acceptable-use': 'ACCEPTABLE_USE_POLICY', 'ai-transparency': 'AI_TRANSPARENCY_NOTICE', 'video-surveillance': 'VIDEO_SURVEILLANCE_NOTICE', dpa: 'DATA_PROCESSING_AGREEMENT', subprocessors: 'SUBPROCESSOR_LIST', 'data-retention': 'DATA_RETENTION_POLICY', security: 'SECURITY_POLICY', 'account-deletion': 'ACCOUNT_DELETION_POLICY', 'incident-response': 'SECURITY_INCIDENT_POLICY',
};

export default function LegalPage({ params }: { params: Promise<{ slug: string }> }) {
  const [document, setDocument] = useState<{ title: string; content: string; version: string; effectiveAt?: string } | null>(null);
  const [slug, setSlug] = useState('');
  const type = types[slug];

  useEffect(() => {
    params.then(({ slug: routeSlug }) => setSlug(routeSlug));
  }, [params]);

  useEffect(() => {
    if (!type) return;
    fetch(`${API}/legal/documents/${type}`).then((response) => response.ok ? response.json() : Promise.reject()).then(setDocument).catch(() => undefined);
  }, [type]);

  return <main className="legal-page"><header className="legal-header"><Link href="/" className="brand"><img src="/logo.png" alt="Sentira" width={40} height={40} /><span>Sentira</span></Link><Link href="/" className="button ghost">Back to Sentira</Link></header><article className="legal-document"><p className="eyebrow">Legal and privacy</p><h1>{document?.title || 'Legal document unavailable'}</h1>{document && <p className="legal-meta">Version {document.version} · Effective date {document.effectiveAt ? new Date(document.effectiveAt).toLocaleDateString() : 'Not specified'}</p>}{document ? <div className="legal-copy">{document.content.split('\n').map((paragraph, index) => paragraph ? <p key={index}>{paragraph}</p> : <br key={index} />)}</div> : <p className="legal-loading">This document is not currently available. The reviewed version must be published by an authorized administrator before it can be displayed.</p>}</article></main>;
}
