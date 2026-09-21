'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, CircleHelp, LoaderCircle, Search, ShieldCheck } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || '/api';
type Account = { accessToken: string; user: { organizationId: string } };
type Manufacturer = { id: string; name: string; description?: string };
type Model = { id: string; manufacturerId: string; name: string; modelNumber: string; deviceType: string; supportedProtocols: Array<{ protocol: string; status: string; verified: boolean }> };
type Guide = { id: string; title: string; description: string; steps: Array<{ id: string; type: string; title: string; body: string; choices?: Array<{ label: string; value: string }> }>; verificationStatus: string };
type Site = { id: string; name: string };
type SetupSession = { id: string; stage: string; completionPercent: number; answers?: Record<string, unknown>; testResult?: { status: string; message: string } };

type DeviceType = 'WIFI_CAMERA' | 'IP_CAMERA' | 'DVR' | 'NVR' | 'CAMERA_SYSTEM' | 'OTHER';

async function api(path: string, token: string, options: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { 'content-type': 'application/json', Authorization: `Bearer ${token}`, ...(options.headers || {}) } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.message || body.error || 'Request failed');
  return body;
}

const deviceTypes: Array<{ value: DeviceType; title: string; description: string }> = [
  { value: 'WIFI_CAMERA', title: 'Single Wi-Fi / IP camera', description: 'One camera that connects directly to your network.' },
  { value: 'IP_CAMERA', title: 'Multiple IP cameras', description: 'Several cameras that connect directly to your network.' },
  { value: 'DVR', title: 'DVR', description: 'Several cameras connected to a recording box.' },
  { value: 'NVR', title: 'NVR', description: 'Network cameras connected to a recording box.' },
  { value: 'CAMERA_SYSTEM', title: 'Complete CCTV system', description: 'A camera system with its own recorder or monitor.' },
  { value: 'OTHER', title: "I'm not sure", description: "That's okay. We'll help identify your system." },
];
const viewingMethods = ['Mobile phone app', 'Computer software', 'TV / monitor', 'Web browser', 'Multiple of these', "I don't know"];

export default function CctvSetupPage() {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [session, setSession] = useState<SetupSession | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [guides, setGuides] = useState<Guide[]>([]);
  const [step, setStep] = useState(1);
  const [deviceType, setDeviceType] = useState<DeviceType | ''>('');
  const [viewingMethod, setViewingMethod] = useState('');
  const [manufacturerId, setManufacturerId] = useState('');
  const [manufacturerSearch, setManufacturerSearch] = useState('');
  const [modelId, setModelId] = useState('');
  const [modelSearch, setModelSearch] = useState('');
  const [siteId, setSiteId] = useState('');
  const [cameraName, setCameraName] = useState('');
  const [streamUrl, setStreamUrl] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [guide, setGuide] = useState<Guide | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [supportCreated, setSupportCreated] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('sentiraAccount');
    if (!saved) { router.replace('/login'); return; }
    const parsed = JSON.parse(saved) as Account;
    setAccount(parsed);
    Promise.all([
      api('/cctv/manufacturers', parsed.accessToken),
      api(`/organizations/${parsed.user.organizationId}/sites`, parsed.accessToken),
      api('/cctv/setup-sessions/active', parsed.accessToken),
    ]).then(async ([manufacturerList, siteList, activeSession]) => {
      const setupSession = activeSession || await api('/cctv/setup-sessions', parsed.accessToken, { method: 'POST', body: JSON.stringify({}) });
      setManufacturers(manufacturerList);
      setSites(siteList);
      setSiteId(siteList[0]?.id || '');
      setSession(setupSession);
      const answers = setupSession.answers || {};
      if (typeof answers.deviceType === 'string') setDeviceType(answers.deviceType as DeviceType);
      if (typeof answers.viewingMethod === 'string') setViewingMethod(answers.viewingMethod);
      if (typeof answers.manufacturerId === 'string') setManufacturerId(answers.manufacturerId);
      if (typeof answers.modelId === 'string') setModelId(answers.modelId);
      setStep(setupSession.stage === 'CONNECT' || setupSession.stage === 'TEST' || setupSession.stage === 'FINISH' ? 5 : setupSession.stage === 'FIND' ? 2 : setupSession.completionPercent >= 35 ? 3 : 1);
    }).catch((caught: Error) => setError(caught.message)).finally(() => setLoading(false));
  }, [router]);

  async function save(patch: Record<string, unknown>) {
    if (!account || !session) return;
    setSaving(true); setError('');
    try { setSession(await api(`/cctv/setup-sessions/${session.id}`, account.accessToken, { method: 'PATCH', body: JSON.stringify(patch) })); }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to save setup progress'); throw caught; }
    finally { setSaving(false); }
  }

  async function selectDevice(value: DeviceType) {
    setDeviceType(value);
    await save({ deviceType: value, stage: 'FIND', currentStep: 'viewing-method', completionPercent: 20, answers: { deviceType: value } });
    setStep(2);
  }

  async function selectViewing(value: string) {
    setViewingMethod(value);
    await save({ stage: 'IDENTIFY', currentStep: 'manufacturer', completionPercent: 35, answers: { deviceType, viewingMethod: value } });
    setStep(3);
  }

  async function selectManufacturer(value: string) {
    setManufacturerId(value);
    if (value === 'unknown') {
      await save({ currentStep: 'model', completionPercent: 50, answers: { deviceType, viewingMethod, manufacturerKnown: false } });
      setStep(4); return;
    }
    const modelList = await api(`/cctv/manufacturers/${value}/models`, account!.accessToken);
    setModels(modelList);
    await save({ manufacturerId: value, currentStep: 'model', completionPercent: 50, answers: { deviceType, viewingMethod, manufacturerId: value } });
    setStep(4);
  }

  async function selectModel(value: string) {
    setModelId(value);
    let modelGuideId: string | undefined;
    if (value !== 'unknown') {
      const modelGuides = await api(`/cctv/models/${value}/guides`, account!.accessToken);
      setGuides(modelGuides);
      setGuide(modelGuides[0] || null);
      modelGuideId = modelGuides[0]?.id;
    }
    await save({ modelId: value === 'unknown' ? undefined : value, guideId: modelGuideId, stage: 'CONNECT', currentStep: 'guide', completionPercent: 65, answers: { deviceType, viewingMethod, manufacturerId: manufacturerId === 'unknown' ? undefined : manufacturerId, modelKnown: value !== 'unknown', modelId: value === 'unknown' ? undefined : value } });
    setStep(5);
  }

  async function submitConnection(event: React.FormEvent) {
    event.preventDefault();
    if (!account || !session || !siteId || !cameraName || !streamUrl) { setError('Add a camera name, location, and secure video address to continue.'); return; }
    setSaving(true); setError('');
    try {
      const test = await api(`/cctv/setup-sessions/${session.id}/test`, account.accessToken, { method: 'POST', body: JSON.stringify({ streamUrl, username, password, protocol: 'rtsp' }) });
      if (test.status !== 'VERIFIED_CONNECTED') throw new Error(test.message || 'Sentira could not verify this camera connection');
      const camera = await api('/cameras/onboarding/manual', account.accessToken, { method: 'POST', body: JSON.stringify({ name: cameraName, siteId, streamUrl, username, password }) });
      await api(`/cctv/setup-sessions/${session.id}/complete`, account.accessToken, { method: 'POST', body: JSON.stringify({ cameraId: camera.id }) });
      router.push('/dashboard');
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Sentira could not finish this setup'); }
    finally { setSaving(false); }
  }

  async function requestHelp() {
    if (!account || !session) return;
    setSaving(true); setError('');
    try {
      await api('/cctv/support-requests', account.accessToken, { method: 'POST', body: JSON.stringify({ setupSessionId: session.id, siteId: siteId || undefined, reason: deviceType === 'DVR' ? 'DVR_SETUP' : deviceType === 'NVR' ? 'NVR_SETUP' : 'SETUP_HELP', message: 'Customer requested help during guided CCTV setup.', context: { deviceType, viewingMethod, manufacturerId: manufacturerId === 'unknown' ? undefined : manufacturerId, modelId: modelId === 'unknown' ? undefined : modelId, currentStep: step } }) });
      setSupportCreated(true);
      await save({ status: 'SUPPORT_REQUESTED' });
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to contact support'); }
    finally { setSaving(false); }
  }

  if (!account || loading) return <main className="shell"><section className="card"><LoaderCircle className="onboarding-spinner" /> Preparing your CCTV setup...</section></main>;
  const visibleManufacturers = manufacturers.filter((item) => item.name.toLowerCase().includes(manufacturerSearch.toLowerCase()));
  const visibleModels = models.filter((item) => `${item.name} ${item.modelNumber}`.toLowerCase().includes(modelSearch.toLowerCase()));

  return <main className="shell">
    <header className="topbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
      <div><p className="eyebrow">Sentira CCTV setup</p><h1 style={{ margin: '8px 0 0' }}>Let&apos;s connect your CCTV</h1></div>
      <button type="button" className="button ghost" onClick={() => router.push('/dashboard')}><ArrowLeft size={16} /> Dashboard</button>
    </header>
    <section className="panel" style={{ maxWidth: 760, margin: '0 auto' }}>
      <div className="progress-track"><div style={{ width: `${Math.max(step * 20, session?.completionPercent || 0)}%` }} /></div>
      <p className="muted">Step {step} of 5 · {['Identify', 'Find', 'Connect', 'Test', 'Finish'][Math.min(step - 1, 4)]}</p>
      {error && <div className="notice offline">{error}<button type="button" className="button ghost" onClick={requestHelp}><CircleHelp size={16} /> Get Sentira help</button></div>}
      {supportCreated && <div className="notice"><ShieldCheck size={18} /> Your support request is open. Sentira has saved your answers so you do not need to explain everything again.</div>}

      {step === 1 && <div className="auth-form"><h2>What are you connecting?</h2><p className="muted">Don&apos;t worry if you don&apos;t know the technical details. We&apos;ll guide you.</p>{deviceTypes.map((item) => <button type="button" className="button secondary" key={item.value} disabled={saving} onClick={() => selectDevice(item.value)}><strong>{item.title}</strong><small>{item.description}</small></button>)}</div>}
      {step === 2 && <div className="auth-form"><h2>How do you watch your cameras?</h2><p className="muted">Choose the option you use most often. “I don&apos;t know” is okay.</p>{viewingMethods.map((item) => <button type="button" className="button secondary" key={item} disabled={saving} onClick={() => selectViewing(item)}>{item}</button>)}</div>}
      {step === 3 && <div className="auth-form"><h2>Who made your camera or recorder?</h2><p className="muted">Choose “I don&apos;t know” if you cannot find the name.</p><label><Search size={16} /> Search manufacturers<input value={manufacturerSearch} onChange={(event) => setManufacturerSearch(event.target.value)} placeholder="e.g. CP PLUS" /></label><div className="choice-grid">{visibleManufacturers.map((item) => <button type="button" className="button secondary" key={item.id} onClick={() => selectManufacturer(item.id)}>{item.name}</button>)}</div><button type="button" className="button ghost" onClick={() => selectManufacturer('unknown')}>I don&apos;t know</button></div>}
      {step === 4 && <div className="auth-form"><h2>Which model do you have?</h2><p className="muted">You can find this on the camera label or recorder screen. It is okay not to know.</p>{manufacturerId !== 'unknown' && <label><Search size={16} /> Search models<input value={modelSearch} onChange={(event) => setModelSearch(event.target.value)} placeholder="Model number or name" /></label>}<div className="choice-grid">{visibleModels.map((item) => <button type="button" className="button secondary" key={item.id} onClick={() => selectModel(item.id)}>{item.name}<small>{item.modelNumber}</small></button>)}</div><button type="button" className="button ghost" onClick={() => selectModel('unknown')}>My model isn&apos;t listed / I don&apos;t know</button><button type="button" className="button ghost" onClick={() => setStep(3)}><ArrowLeft size={16} /> Back</button></div>}
      {step === 5 && <div className="auth-form"><h2>{guide?.title || 'Let Sentira connect your camera'}</h2><p className="muted">{guide?.description || 'We do not have verified model-specific instructions yet. We will only ask for a video address if your system already provides one.'}</p>{guide && <div className="guide-steps">{guide.steps.slice(0, 3).map((guideStep) => <article className="card" key={guideStep.id}><strong>{guideStep.title}</strong><p>{guideStep.body}</p></article>)}</div>}<p className="notice">Technical details stay hidden until they are needed. Your camera password is encrypted and is never shown after submission.</p><form onSubmit={submitConnection}><label>Camera name<input required value={cameraName} onChange={(event) => setCameraName(event.target.value)} placeholder="e.g. Front Door" /></label><label>Location<select required value={siteId} onChange={(event) => setSiteId(event.target.value)}><option value="">Choose a location</option>{sites.map((site) => <option value={site.id} key={site.id}>{site.name}</option>)}</select></label><label>Secure video address<input required value={streamUrl} onChange={(event) => setStreamUrl(event.target.value)} placeholder="Only if your manufacturer provided one" /></label><label>Username <span className="muted">(if required)</span><input value={username} onChange={(event) => setUsername(event.target.value)} /></label><label>Password <span className="muted">(if required)</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label><button type="submit" className="button" disabled={saving}>{saving ? 'Checking connection...' : 'Test and add camera'} <ArrowRight size={16} /></button></form><button type="button" className="button ghost" disabled={saving} onClick={requestHelp}><CircleHelp size={16} /> I need help instead</button></div>}
    </section>
  </main>;
}
