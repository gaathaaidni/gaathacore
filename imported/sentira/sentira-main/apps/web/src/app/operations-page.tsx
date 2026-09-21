'use client';
import { useEffect, useState } from 'react';
export function OperationsPage({ title, endpoint }: { title: string; endpoint: string }) {
  const [state,setState]=useState<'loading'|'error'|'empty'|'ready'>('loading'); const [data,setData]=useState<any>(null);
  useEffect(()=>{ const token=localStorage.getItem('accessToken'); fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api'}${endpoint}`,{headers:token?{Authorization:`Bearer ${token}`}:{}}).then(async r=>{if(!r.ok)throw new Error();const body=await r.json();setData(body);setState(Array.isArray(body)&&!body.length?'empty':'ready')}).catch(()=>setState('error')); },[endpoint]);
  return <main className="shell"><section className="hero"><p>Sentira Operations</p><h1>{title}</h1><span>Organization-scoped live API data</span></section>{state==='loading'&&<section className="card">Loading operational data…</section>}{state==='error'&&<section className="card offline">Unable to load data. Authenticate and confirm API availability.</section>}{state==='empty'&&<section className="card">No records match the selected scope.</section>}{state==='ready'&&<pre className="card">{JSON.stringify(data,null,2)}</pre>}</main>;
}
