'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Camera as CameraIcon, CheckCircle2, LoaderCircle, QrCode, Search, Settings2, Video } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || '/api';
type Account = { accessToken: string; refreshToken: string; user: { organizationId: string; email: string } };
type Camera = { id: string; name: string; status: string; aiProcessingStatus: string };
type EventItem = { id: string; eventType: string; severity: string; status: string; createdAt: string };
type OnboardingSession = { id: string; method: string; status: string; pairingCode?: string; expiresAt: string; connectorRequired?: boolean };
type DiscoveredCamera = { id: string; name: string; manufacturer?: string; model?: string; discoveryStatus: string };

function cameraStatus(status: string) {
  const labels: Record<string, string> = { online: 'Connected', connecting: 'Connecting', offline: 'Camera unavailable', error: 'Connection problem', ai_processing: 'Processing', disabled: 'Disabled' };
  return labels[status] || 'Connection problem';
}

async function api(path: string, token: string, options: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'content-type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.message || body.error || 'Request failed') as Error & { code?: string };
    error.code = body.code || body.response?.code;
    throw error;
  }
  return body;
}

export default function DashboardPage() {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [siteId, setSiteId] = useState('');
  const [sites, setSites] = useState<{ id: string; name: string }[]>([]);
  const [siteName, setSiteName] = useState('');
  const [cameraForm, setCameraForm] = useState({ name: '', streamUrl: '', username: '', password: '' });
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [organization, setOrganization] = useState<{ name: string; plan: string; cameraLimit: number } | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [wizardMode, setWizardMode] = useState<'choose' | 'automatic' | 'qr' | 'dvr_nvr' | 'advanced'>('choose');
  const [onboardingSession, setOnboardingSession] = useState<OnboardingSession | null>(null);
  const [discoveredCameras, setDiscoveredCameras] = useState<DiscoveredCamera[]>([]);
  const [onboardingLoading, setOnboardingLoading] = useState(false);
  const [cameraLoading, setCameraLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('sentiraAccount');
    if (!saved) {
      router.replace('/login');
      return;
    }
    setAccount(JSON.parse(saved) as Account);
  }, [router]);

  useEffect(() => {
    if (!account) return;
    setState('loading');
    Promise.all([
      api(`/organizations/${account.user.organizationId}`, account.accessToken),
      api(`/organizations/${account.user.organizationId}/sites`, account.accessToken),
      api('/cameras', account.accessToken),
      api('/events', account.accessToken),
      api('/dashboard/stats', account.accessToken),
    ])
      .then(([org, siteList, cameraList, eventList, dashboard]) => {
        setOrganization(org);
        setSites(siteList);
        setSiteId(siteList[0]?.id || '');
        setCameras(cameraList);
        setEvents(eventList);
        setStats(dashboard);
        setState('ready');
      })
      .catch((error: Error) => {
        setMessage(error.message);
        setState('error');
      });
  }, [account]);

  async function addSite(event: React.FormEvent) {
    event.preventDefault();
    if (!account || !siteName) return;
    try {
      const site = await api(`/organizations/${account.user.organizationId}/sites`, account.accessToken, {
        method: 'POST',
        body: JSON.stringify({ name: siteName }),
      });
      setSites([...sites, site]);
      setSiteId(site.id);
      setSiteName('');
      setMessage('Site created.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to create site');
    }
  }

  async function addCamera(event: React.FormEvent) {
    event.preventDefault();
    if (!account || !siteId) {
      setMessage('Please choose a site first.');
      return;
    }
    setCameraLoading(true);
    setMessage('');
    try {
      await api('/cameras/onboarding/manual', account.accessToken, {
        method: 'POST',
        body: JSON.stringify({ ...cameraForm, siteId, protocol: 'rtsp' }),
      });
      setCameraForm({ name: '', streamUrl: '', username: '', password: '' });
      setWizardMode('choose');
      setMessage('Camera added. Sentira will begin connecting to it.');
      setCameras(await api('/cameras', account.accessToken));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to add camera');
    } finally {
      setCameraLoading(false);
    }
  }

  async function startOnboarding(method: 'automatic' | 'qr' | 'dvr_nvr') {
    if (!account) return;
    setOnboardingLoading(true);
    setMessage('');
    try {
      const session = await api('/cameras/onboarding/sessions', account.accessToken, { method: 'POST', body: JSON.stringify({ method }) });
      setOnboardingSession(session);
      setDiscoveredCameras([]);
      setWizardMode(method);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to start camera setup');
    } finally {
      setOnboardingLoading(false);
    }
  }

  async function refreshOnboarding() {
    if (!account || !onboardingSession) return;
    setOnboardingLoading(true);
    try {
      const session = await api(`/cameras/onboarding/sessions/${onboardingSession.id}`, account.accessToken);
      setOnboardingSession(session);
      if (session.status === 'connected') {
        const result = await api(`/cameras/onboarding/sessions/${session.id}/discovered-cameras`, account.accessToken);
        setDiscoveredCameras(result.cameras || []);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to check camera setup');
    } finally {
      setOnboardingLoading(false);
    }
  }

  async function claimDiscoveredCamera(camera: DiscoveredCamera) {
    if (!account || !onboardingSession || !siteId) {
      setMessage('Choose a camera location before adding a discovered camera.');
      return;
    }
    setOnboardingLoading(true);
    setMessage('');
    try {
      await api(`/cameras/onboarding/discovered-cameras/${camera.id}/claim`, account.accessToken, {
        method: 'POST',
        body: JSON.stringify({ siteId, name: camera.name }),
      });
      setCameras(await api('/cameras', account.accessToken));
      setDiscoveredCameras(discoveredCameras.filter((item) => item.id !== camera.id));
      setMessage(`${camera.name} is now connected to Sentira.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to add discovered camera');
    } finally {
      setOnboardingLoading(false);
    }
  }

  if (!account) return null;
  const limit = organization?.cameraLimit ?? 0;

  return (
    <main className="shell">
      <header className="topbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <p className="eyebrow">Sentira workspace</p>
          <h1 style={{ margin: '8px 0 0' }}>{organization?.name || 'Loading workspace'}</h1>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="button" className="button ghost" onClick={() => router.push('/cctv/help')}>CCTV Help Center</button>
          <button type="button" className="button" onClick={() => router.push('/cctv')}>Add CCTV</button>
          <button type="button" className="button ghost" onClick={() => { localStorage.removeItem('sentiraAccount'); router.replace('/login'); }}>Log out</button>
        </div>
      </header>

      {state === 'loading' && <section className="card">Loading live workspace data...</section>}
      {state === 'error' && <section className="card offline">{message || 'Unable to load the workspace.'}</section>}

      {state === 'ready' && (
        <>
          <section className="metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 18 }}>
            <article className="card"><small>Plan</small><strong>{organization?.plan}</strong></article>
            <article className="card"><small>Cameras</small><strong>{cameras.length} / {limit}</strong></article>
            <article className="card"><small>Online</small><strong>{stats?.cameras?.online ?? 0}</strong></article>
            <article className="card"><small>Open events</small><strong>{stats?.events?.unresolved ?? 0}</strong></article>
          </section>

          <section className="workspace-grid" style={{ display: 'grid', gridTemplateColumns: '1.4fr 0.8fr', gap: 18, marginTop: 18 }}>
            <div>
              <section className="panel" style={{ display: 'grid', gap: 18 }}>
                <div className="panel-heading">
                  <h2>Cameras</h2>
                  <span>{cameras.length} / {limit} cameras used</span>
                </div>
                {cameras.length === 0 ? (
                  <p className="muted">No cameras configured yet.</p>
                ) : (
                  cameras.map((camera) => (
                    <article className="list-row" key={camera.id} style={{ borderBottom: '1px solid rgba(148,163,184,0.2)', paddingBottom: 8 }}>
                      <div>
                        <strong>{camera.name}</strong>
                        <small>{cameraStatus(camera.status)} · AI {camera.aiProcessingStatus === 'processing' ? 'Processing' : 'Ready'}</small>
                      </div>
                    </article>
                  ))
                )}
                {cameras.length >= limit && <p className="notice">Your free plan includes up to {limit} cameras. Contact us to add additional cameras.</p>}
              </section>

              <section className="panel" style={{ display: 'grid', gap: 18, marginTop: 18 }}>
                <div className="panel-heading"><h2>Events</h2><span>{events.length} live records</span></div>
                {events.length === 0 ? <p className="muted">No events in this organization.</p> : events.slice(0, 10).map((item) => (
                  <article className="list-row" key={item.id} style={{ borderBottom: '1px solid rgba(148,163,184,0.2)', paddingBottom: 8 }}>
                    <div><strong>{item.eventType}</strong><small>{item.severity} · {item.status} · {new Date(item.createdAt).toLocaleString()}</small></div>
                  </article>
                ))}
              </section>
            </div>

            <aside style={{ display: 'grid', gap: 18 }}>
              <section className="panel">
                <div className="panel-heading">
                  <h2>Camera location</h2>
                </div>
                <form onSubmit={addSite} className="auth-form">
                  <p className="muted">Where is this camera located? We will use this as its site.</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {['Home', 'Office', 'Shop', 'Warehouse'].map((name) => <button key={name} type="button" className="button ghost" onClick={() => setSiteName(name)}>{name}</button>)}
                  </div>
                  <label>
                    Or name a location
                    <input value={siteName} onChange={(e) => setSiteName(e.target.value)} placeholder="e.g. Main office" />
                  </label>
                  <button type="submit" className="button">Create site</button>
                </form>
              </section>

              <section className="panel">
                <div className="panel-heading">
                  <h2>Add your camera</h2>
                  <span>Connect your CCTV to Sentira</span>
                </div>
                {wizardMode === 'choose' && <div className="auth-form">
                  <p className="muted">Let&apos;s connect your CCTV. You don&apos;t need to know technical settings.</p>
                  <button type="button" className="button" disabled={onboardingLoading} onClick={() => startOnboarding('automatic')}><Search size={18} /> Connect automatically <small>Recommended</small></button>
                  <button type="button" className="button secondary" onClick={() => startOnboarding('qr')}><QrCode size={18} /> I have a QR code</button>
                  <button type="button" className="button secondary" onClick={() => startOnboarding('dvr_nvr')}><Video size={18} /> My cameras use a DVR / NVR</button>
                  <button type="button" className="button ghost" onClick={() => setWizardMode('advanced')}><Settings2 size={18} /> Advanced connection</button>
                </div>}
                {wizardMode !== 'choose' && wizardMode !== 'advanced' && <div className="auth-form">
                  <button type="button" className="button ghost" onClick={() => setWizardMode('choose')}><ArrowLeft size={16} /> Back to options</button>
                  <div style={{ display: 'grid', gap: 12, padding: '8px 0' }}>
                    <LoaderCircle size={30} className="onboarding-spinner" />
                    <h3>{wizardMode === 'automatic' ? 'Looking for your cameras' : wizardMode === 'qr' ? 'Scan your camera QR code' : 'Connect your DVR / NVR'}</h3>
                    <p className="muted">Make sure your CCTV system is powered on. A Sentira Connector inside your network is required for local camera discovery.</p>
                    {onboardingSession?.pairingCode && <div className="card" style={{ textAlign: 'center' }}><small>Pairing code</small><strong style={{ display: 'block', fontSize: 28, letterSpacing: 3 }}>{onboardingSession.pairingCode}</strong><span className="muted">Enter this code in the Sentira Connector app.</span></div>}
                    {onboardingSession?.status === 'connected' && <p><CheckCircle2 size={18} /> Connected. Cameras found will appear here.</p>}
                    {discoveredCameras.length > 0 && <div style={{ display: 'grid', gap: 10 }}>
                      <h3>Cameras found</h3>
                      {discoveredCameras.map((camera) => <article className="list-row" key={camera.id}>
                        <div><strong>{camera.name}</strong><small>{camera.manufacturer || 'Camera'}{camera.model ? ` · ${camera.model}` : ''} · Ready</small></div>
                        <button type="button" className="button" disabled={onboardingLoading} onClick={() => claimDiscoveredCamera(camera)}>Use this camera</button>
                      </article>)}
                    </div>}
                  </div>
                  <button type="button" className="button secondary" disabled={onboardingLoading} onClick={refreshOnboarding}>{onboardingLoading ? 'Checking...' : 'Check connection'}</button>
                  <p className="muted">The connector uses an outbound connection. You do not need to open router ports.</p>
                </div>}
                {wizardMode === 'advanced' && <form onSubmit={addCamera} className="auth-form">
                  <button type="button" className="button ghost" onClick={() => setWizardMode('choose')}><ArrowLeft size={16} /> Back to options</button>
                  <p className="muted">Only use this if you already have your camera&apos;s stream address.</p>
                  <label>Camera name<input required value={cameraForm.name} onChange={(e) => setCameraForm({ ...cameraForm, name: e.target.value })} placeholder="e.g. Front Door" /></label>
                  <label>Camera link<input required value={cameraForm.streamUrl} onChange={(e) => setCameraForm({ ...cameraForm, streamUrl: e.target.value })} placeholder="rtsp://..." /></label>
                  <label>Username<input value={cameraForm.username} onChange={(e) => setCameraForm({ ...cameraForm, username: e.target.value })} /></label>
                  <label>Password<input type="password" value={cameraForm.password} onChange={(e) => setCameraForm({ ...cameraForm, password: e.target.value })} /></label>
                  <label>Location<select required value={siteId} onChange={(e) => setSiteId(e.target.value)}><option value="">Choose a location</option>{sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}</select></label>
                  <button type="submit" className="button"><CameraIcon size={18} /> Add camera</button>
                </form>}
              </section>
            </aside>
          </section>
        </>
      )}
      {message && <p className="auth-message error" style={{ marginTop: 18 }}>{message}</p>}
    </main>
  );
}
