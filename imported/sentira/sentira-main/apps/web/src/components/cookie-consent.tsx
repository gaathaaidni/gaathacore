'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api';
type Categories = { necessary: boolean; preferences: boolean; analytics: boolean; marketing: boolean };
const defaultCategories: Categories = { necessary: true, preferences: false, analytics: false, marketing: false };
const storageKey = 'sentiraCookieConsent';

function sessionId() {
  const key = 'sentiraConsentSession';
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const value = crypto.randomUUID();
  localStorage.setItem(key, value);
  return value;
}

export function CookieConsent() {
  const [categories, setCategories] = useState<Categories | null>(null);
  const [manage, setManage] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try { setCategories(JSON.parse(saved)); } catch { setCategories(null); }
    }
  }, []);

  async function save(next: Categories) {
    setCategories(next);
    setManage(false);
    localStorage.setItem(storageKey, JSON.stringify(next));
    await fetch(`${API}/legal/cookie-consent`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ sessionId: sessionId(), categories: next, cookiePolicyVersion: '1.0' }),
    }).catch(() => undefined);
  }

  if (categories && !manage) {
    return <button className="cookie-settings-link" type="button" onClick={() => setManage(true)}>Cookie settings</button>;
  }

  return (
    <aside className="cookie-consent" aria-label="Cookie consent">
      <div>
        <p className="eyebrow">Privacy choices</p>
        <h2>Cookies and similar technologies</h2>
        <p>Necessary storage keeps Sentira secure and working. Optional choices help with preferences, analytics, or marketing only after you choose them.</p>
        <Link href="/privacy">Read the Privacy Policy</Link>
      </div>
      {manage && <div className="cookie-options">
        {(['preferences', 'analytics', 'marketing'] as const).map((category) => (
          <label key={category}><input type="checkbox" checked={Boolean(categories?.[category])} onChange={(event) => setCategories({ ...(categories || defaultCategories), [category]: event.target.checked })} /> {category[0].toUpperCase() + category.slice(1)}</label>
        ))}
      </div>}
      <div className="cookie-actions">
        <button className="button secondary" type="button" onClick={() => save({ ...defaultCategories, ...(categories || {}) })}>Accept all</button>
        <button className="button ghost" type="button" onClick={() => save(defaultCategories)}>Reject optional</button>
        <button className="button ghost" type="button" onClick={() => setManage(true)}>{manage ? 'Review choices' : 'Manage preferences'}</button>
        {manage && <button className="button" type="button" onClick={() => save(categories || defaultCategories)}>Save choices</button>}
      </div>
    </aside>
  );
}
