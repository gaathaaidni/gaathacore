'use client';

import Link from 'next/link';
import {
  BellRing,
  Building2,
  Camera,
  Cpu,
  DatabaseZap,
  Gauge,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react';
import { useEffect, useState } from 'react';

const navItems = [
  { label: 'Home', href: '#top' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Features', href: '#features' },
  { label: 'Industries', href: '#industries' },
  { label: 'Security', href: '#security' },
  { label: 'About', href: '#about' },
];

const steps = [
  { title: 'Connect', description: 'Connect existing CCTV and RTSP camera feeds into the Sentira platform.' },
  { title: 'Understand', description: 'Sentira analyzes incoming frames and sensor data with AI-assisted visual processing.' },
  { title: 'Detect', description: 'Rules and detections identify relevant events, conditions, and operational signals.' },
  { title: 'Alert', description: 'Authorized teams receive event updates and alerts based on their organization and permissions.' },
  { title: 'Decide', description: 'Humans review the event and take the appropriate action with context and evidence.' },
];

const features = [
  { icon: Camera, title: 'Intelligent Camera Monitoring', text: 'Monitor multiple camera feeds from a single operational view and keep your surveillance work organized.' },
  { icon: Cpu, title: 'AI-Powered Detection', text: 'Analyze live video frames and identify configured visual conditions relevant to your environment.' },
  { icon: Workflow, title: 'Rule-Based Events', text: 'Define event rules around supported detection conditions to surface the situations that matter.' },
  { icon: Gauge, title: 'Real-Time Events', text: 'Generate and review events through the platform’s event infrastructure as conditions are recognized.' },
  { icon: Building2, title: 'Multi-Tenant Organizations', text: 'Keep each organization and its cameras isolated with structure designed for tenant-level separation.' },
  { icon: LockKeyhole, title: 'Camera Entitlements', text: 'Apply organization-scoped camera limits and review entitlement constraints in a controlled environment.' },
  { icon: ShieldCheck, title: 'Secure Camera Credentials', text: 'Protect sensitive camera credentials and avoid exposing them unnecessarily in public responses or UI.' },
  { icon: DatabaseZap, title: 'Evidence', text: 'Associate relevant events with stored visual evidence where supported by the current event-media workflow.' },
  { icon: BellRing, title: 'Alerts & Notifications', text: 'Deliver operational awareness to the right users with alerts, updates, and event-driven notification patterns.' },
];

const industries = [
  'Restaurants',
  'Retail',
  'Warehouses',
  'Offices',
  'Hospitality',
  'Manufacturing',
  'Custom Deployments',
];

const securityPoints = [
  'Organization-level tenant isolation and scoped access design',
  'JWT authentication and role-based access enforcement',
  'Camera credential redaction and controlled exposure',
  'Organization-scoped event and evidence access',
  'Authorized WebSocket event delivery for relevant users',
  'Internal service networking and restricted operational boundaries',
  'Secure evidence access patterns for tenant-aware retrieval',
  'Audit logging and operational review architecture',
];

const compareRows = [
  { label: 'Traditional CCTV', items: ['Records video', 'Requires constant human monitoring', 'Difficult to search and review', 'Important events can be missed'] },
  { label: 'Sentira AI', items: ['Understands configured visual conditions', 'Surfaces relevant events', 'Centralizes monitoring', 'Keeps humans in control of decisions'] },
];

export default function HomePage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('sentiraAccount');
    setIsAuthenticated(Boolean(saved));
  }, []);

  return (
    <main className="landing-page" id="top">
      <header className="site-header">
        <div className="site-header-inner">
          <Link href="/" className="brand" aria-label="Sentira AI home">
            <span className="brand-mark">
              <img src="/logo.png" alt="Sentira AI logo" width={40} height={40} />
            </span>
            <span className="brand-text">Sentira AI</span>
          </Link>

          <nav className="nav-links" aria-label="Main navigation">
            {navItems.map((item) => (
              <Link key={item.label} href={item.href}>{item.label}</Link>
            ))}
          </nav>

          <div className="nav-actions">
            {isAuthenticated ? (
              <Link href="/dashboard" className="button secondary">Open Dashboard</Link>
            ) : (
              <>
                <Link href="/login" className="button ghost">Login</Link>
                <Link href="/signup" className="button">Get Started</Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="hero-section">
        <div className="container hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">AI video intelligence</span>
            <h1>Your Cameras Watch.<br />Sentira Understands.</h1>
            <p>
              Sentira AI transforms ordinary CCTV camera feeds into intelligent visual monitoring systems that detect events,
              understand activity, and deliver actionable alerts in real time.
            </p>
            <div className="hero-actions">
              <Link href="/signup" className="cta-button">Get Started</Link>
              <Link href="#how-it-works" className="button secondary">See How It Works</Link>
            </div>
            <div className="hero-meta">
              <span><Camera size={16} /> Multi-camera monitoring</span>
              <span><Sparkles size={16} /> AI-assisted inspection</span>
              <span><BellRing size={16} /> Event alerts</span>
            </div>
          </div>

          <div className="hero-visual" aria-label="Sentira workflow illustration">
            <div className="visual-panel">
              <div className="flow-row">
                <span className="flow-chip">Cameras</span>
                <span className="flow-arrow">→</span>
                <span className="flow-chip">AI</span>
              </div>
              <div className="flow-row">
                <span className="flow-chip">Understand</span>
                <span className="flow-arrow">→</span>
                <span className="flow-chip">Events</span>
              </div>
              <div className="flow-row">
                <span className="flow-chip">Alerts</span>
                <span className="flow-arrow">→</span>
                <span className="flow-chip">Human Review</span>
              </div>

              <div className="signal-card">
                <div className="signal-top">
                  <span>Operational signal</span>
                  <strong>74%</strong>
                </div>
                <div className="signal-bar"><span /></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">From video surveillance to visual intelligence</span>
            <h2>Traditional CCTV records what happened. Sentira helps organizations understand what matters.</h2>
          </div>
          <div className="two-col">
            <div className="card-panel">
              <h3>Built for organizations that already have cameras</h3>
              <p>
                Many businesses already have security cameras installed but lack the operational intelligence to interpret them at scale.
                Sentira brings structure to the stream: live monitoring, event detection, contextual review, and organization-aware access.
              </p>
            </div>
            <div className="card-panel">
              <h3>Intelligence without constant manual watching</h3>
              <p>
                Instead of relying on teams to stare at camera feeds around the clock, the platform helps identify important conditions,
                highlight signals, and surface relevant events for human review.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="how-it-works">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">How it works</span>
            <h2>See how camera data becomes useful operational insight.</h2>
          </div>
          <div className="step-list">
            {steps.map((step, index) => (
              <article key={step.title} className="step-card">
                <span className="step-number">{index + 1}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="features">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">Features</span>
            <h2>Practical monitoring capabilities for modern operations.</h2>
          </div>
          <div className="feature-grid">
            {features.map(({ icon: Icon, title, text }) => (
              <article key={title} className="card-panel">
                <span className="icon-wrap"><Icon size={18} /></span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="industries">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">Industries & use cases</span>
            <h2>Flexible monitoring for the environments organizations already operate.</h2>
          </div>
          <div className="industry-grid">
            {industries.map((industry) => (
              <article key={industry} className="industry-card">
                <h3>{industry}</h3>
                <p>
                  {industry === 'Restaurants' && 'Monitor service zones, operations, and configured activity patterns across dining and back-of-house spaces.'}
                  {industry === 'Retail' && 'Track customer-facing areas, operational activity, and relevant visual conditions using configured monitoring rules.'}
                  {industry === 'Warehouses' && 'Monitor zones, movement, and operational conditions across active facilities and logistics workflows.'}
                  {industry === 'Offices' && 'Watch shared areas and designated spaces for access patterns and operational awareness.'}
                  {industry === 'Hospitality' && 'Observe guest-facing and service areas with context-aware monitoring for operational teams.'}
                  {industry === 'Manufacturing' && 'Support production and operational oversight with visual monitoring of active workspaces and zones.'}
                  {industry === 'Custom Deployments' && 'Adapt Sentira to organization-specific cameras, zones, and rules that match your operational environment.'}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="about">
        <div className="container">
          <div className="banner">
            <h3>Stop watching every camera. Start understanding what matters.</h3>
            <p>
              Sentira gives operational teams a calmer, clearer way to monitor their environments: connect existing cameras,
              define relevant conditions, and focus attention on the events that deserve a response.
            </p>
            <div className="banner-actions">
              <Link href="/signup" className="button">Get Started</Link>
              <Link href="/login" className="button secondary">Login</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="security">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">Security</span>
            <h2>Designed with security and tenant isolation as core architectural principles.</h2>
          </div>
          <div className="security-grid">
            <div className="security-card">
              <h3>Access controls</h3>
              <ul>
                {securityPoints.slice(0, 4).map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
            <div className="security-card">
              <h3>Operational boundaries</h3>
              <ul>
                {securityPoints.slice(4, 8).map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
            <div className="security-card">
              <h3>Honest positioning</h3>
              <p>
                Sentira is built to support secure, organization-scoped monitoring and evidence access, but the platform is currently
                positioned as a controlled beta environment for real-world testing and evaluation.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">Why Sentira</span>
            <h2>From passive recording to actionable intelligence.</h2>
          </div>
          <div className="compare-grid">
            {compareRows.map((row) => (
              <article key={row.label} className="compare-card">
                <h3>{row.label}</h3>
                <ul>
                  {row.items.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="eyebrow">Architecture</span>
            <h2>Designed to connect camera streams to operational awareness.</h2>
          </div>
          <div className="arch-grid">
            <div className="arch-visual">
              <div className="arch-card">CCTV Cameras</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-card">Stream Gateway</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-card">AI Processing</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-card">Detection / Rules</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-card">Events</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-card">Evidence / Notifications</div>
              <div className="arch-arrow">↓</div>
              <div className="arch-card">Sentira Dashboard</div>
            </div>
            <div className="card-panel">
              <h3>Platform capability, not marketing overreach</h3>
              <p>
                Sentira is positioned as an AI-assisted monitoring platform for organizations that need to understand what is happening within their
                camera network. It is designed around configurable monitoring, event-driven workflows, tenant boundaries, and evidence-aware review.
              </p>
              <ul className="list-check">
                <li>Multi-camera visibility</li>
                <li>Alert-driven workflow</li>
                <li>Organization-scoped access</li>
                <li>Evidence-aware event handling</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="banner">
            <h3>Be among the first to experience intelligent video monitoring.</h3>
            <p>
              Sentira AI is currently entering controlled beta testing with selected users and organizations. The platform is intended for
              real-world evaluation and operational learning before broader expansion.
            </p>
            <div className="banner-actions">
              <Link href="/signup" className="button">Request Early Access</Link>
              <Link href="#features" className="button secondary">Explore Features</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="banner">
            <h3>Ready to make your cameras smarter?</h3>
            <p>
              Connect your cameras, configure your monitoring rules, and let Sentira help your team focus on the events that matter.
            </p>
            <div className="banner-actions">
              <Link href="/signup" className="button">Get Started</Link>
              <Link href="/login" className="button secondary">Login</Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="footer-inner">
          <div>
            <div className="brand footer-brand">
              <span className="brand-mark">
                <img src="/logo.png" alt="Sentira AI logo" width={40} height={40} />
              </span>
              <span className="brand-text">Sentira AI</span>
            </div>
            <p className="footer-copy">
              Sentira AI helps organizations turn camera feeds into operational intelligence, event awareness, and review-ready monitoring workflows.
            </p>
          </div>
          <div>
            <div className="footer-links">
              <Link href="/">Home</Link>
              <Link href="#how-it-works">How It Works</Link>
              <Link href="#features">Features</Link>
              <Link href="#industries">Industries</Link>
              <Link href="#security">Security</Link>
              <Link href="/login">Login</Link>
              <Link href="/signup">Sign Up</Link>
              <Link href="#top">Privacy Policy</Link>
              <Link href="#top">Terms of Service</Link>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
