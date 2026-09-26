"""Dependency-free, fail-closed public entry page for public Gaatha products.

This directory never probes, proxies, or grants access to a product.  An
operator-supplied URL is necessary but not sufficient for a link: the static
product exposure policy must also explicitly approve public entry.
"""
from __future__ import annotations

import base64
import html
import os
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable
from urllib.parse import urlparse

# Load optimized logo.png if present alongside this file
_LOGO_FILE = os.path.join(os.path.dirname(__file__), "logo.png")
_LOGO_B64 = ""
if os.path.exists(_LOGO_FILE):
    try:
        with open(_LOGO_FILE, "rb") as _f:
            _LOGO_B64 = base64.b64encode(_f.read()).decode("ascii")
    except Exception:
        pass


class PublicEntryState(str, Enum):
    READY = "READY FOR PUBLIC ENTRY"
    CONDITIONAL = "CONDITIONAL / DEPLOYMENT VALIDATION REQUIRED"
    NOT_READY = "NOT READY / DO NOT EXPOSE"


@dataclass(frozen=True)
class ProductExposurePolicy:
    key: str
    name: str
    description: str
    state: PublicEntryState
    reason: str
    required_deployment_validation: str
    url_environment_variable: str | None
    public_entry_approved: bool = False

    @property
    def permits_public_entry(self) -> bool:
        """Only an explicit, code-reviewed READY approval permits a link."""
        return self.state is PublicEntryState.READY and self.public_entry_approved


@dataclass(frozen=True)
class PublicProduct:
    policy: ProductExposurePolicy
    entry_url: str | None

    @property
    def name(self) -> str:
        return self.policy.name

    @property
    def description(self) -> str:
        return self.policy.description

    @property
    def status(self) -> str:
        return self.policy.state.value


# The bare public hostname is deliberate. ``app.gaatha.tech`` is not an
# accepted alias: accepting it could accidentally direct a user to a separate
# deployment with a different access-control boundary.
PUBLIC_ENTRY_HOST = "gaatha.tech"


PRODUCT_POLICIES = (
    ProductExposurePolicy(
        "suite",
        "Gaatha Suite",
        "Enterprise-grade business operations, multi-entity finances, HRM, CRM, and automated invoicing.",
        PublicEntryState.CONDITIONAL,
        "Authentication and organization-aware controls exist in source, but route-wide tenant isolation and the deployed public handoff are not proven.",
        "Validate the HTTPS entry path, unauthenticated login handoff, and two-organization negative access checks across deployed protected routes.",
        "GAATHA_SUITE_PUBLIC_URL",
    ),
    ProductExposurePolicy(
        "pos",
        "Gaatha POS",
        "Next-generation restaurant & retail point-of-sale with real-time KDS, table mapping, and live inventory sync.",
        PublicEntryState.CONDITIONAL,
        "Flask login, restaurant ownership, and RBAC evidence exists in source, but deployed routing and complete tenant-negative coverage are unverified.",
        "Validate the HTTPS entry path, login redirect/API unauthorized behavior, and two-restaurant negative checks for POS, KDS, admin, and API routes.",
        "GAATHA_POS_PUBLIC_URL",
    ),
    ProductExposurePolicy(
        "sentira",
        "Sentira",
        "AI-powered visual intelligence and CCTV surveillance platform with ultra-low latency streams and event detection.",
        PublicEntryState.CONDITIONAL,
        "Phase 21 preserves a live-media gate; static/API evidence does not prove deployed media isolation or browser playback.",
        "Validate MediaMTX authentication, HLS, WHEP, browser playback, two-tenant live isolation, lifecycle/revocation, and real/remote camera behavior.",
        "GAATHA_SENTIRA_PUBLIC_URL",
    ),
)
PUBLIC_PATHS = {"/", "/about", "/contact", "/terms", "/privacy", "/user-policy", "/healthz"}


def approved_public_url(value: str | None) -> str | None:
    """Accept only an explicit HTTPS URL on the public launch host."""
    if not value:
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    if parsed.hostname.lower() != PUBLIC_ENTRY_HOST:
        return None
    return value.strip()


def configured_products(environ: dict[str, str] | None = None) -> tuple[PublicProduct, ...]:
    environ = os.environ if environ is None else environ
    return tuple(
        PublicProduct(
            policy,
            approved_public_url(environ.get(policy.url_environment_variable))
            if policy.permits_public_entry and policy.url_environment_variable
            else None,
        )
        for policy in PRODUCT_POLICIES
    )


CSS_STYLES = """
:root {
  --bg-dark: #070a13;
  --bg-card: rgba(16, 24, 40, 0.72);
  --bg-card-hover: rgba(26, 38, 64, 0.85);
  --border-card: rgba(255, 255, 255, 0.08);
  --border-card-hover: rgba(99, 102, 241, 0.45);
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --accent-blue: #3b82f6;
  --accent-cyan: #06b6d4;
  --accent-purple: #8b5cf6;
  --accent-gradient: linear-gradient(135deg, #38bdf8 0%, #6366f1 50%, #a855f7 100%);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-dark);
  background-image: 
    radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.14) 0%, transparent 40%),
    radial-gradient(circle at 85% 70%, rgba(139, 92, 246, 0.14) 0%, transparent 45%),
    linear-gradient(180deg, #070a13 0%, #0d1322 100%);
  color: var(--text-main);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.container {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

header {
  padding: 1.5rem 0 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(7, 10, 19, 0.7);
  backdrop-filter: blur(14px);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  text-decoration: none;
  color: inherit;
}

.brand-logo {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.45));
  transition: transform 0.3s ease;
}

.brand:hover .brand-logo {
  transform: rotate(5deg) scale(1.05);
}

.brand-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.badge-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.85rem;
  border-radius: 9999px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.hero {
  padding: 3.5rem 0 2rem;
  text-align: center;
}

.hero h1 {
  font-size: 2.85rem;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.04em;
  margin-bottom: 1rem;
}

.hero-gradient {
  background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero p {
  font-size: 1.12rem;
  color: var(--text-muted);
  max-width: 720px;
  margin: 0 auto 1.5rem;
}

.features-banner {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-top: 1rem;
}

.feat-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
  color: var(--text-dim);
  font-weight: 500;
}

.feat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 6px #38bdf8;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.75rem;
  margin: 2rem 0 3.5rem;
}

.card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 18px;
  padding: 2.25rem 2rem;
  backdrop-filter: blur(16px);
  display: flex;
  flex-direction: column;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.4);
}

.card:hover {
  transform: translateY(-6px);
  border-color: var(--border-card-hover);
  box-shadow: 0 24px 45px -15px rgba(99, 102, 241, 0.3);
  background: var(--bg-card-hover);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.product-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
}

.icon-suite { background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.25)); border: 1px solid rgba(168, 85, 247, 0.4); }
.icon-pos { background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(59, 130, 246, 0.25)); border: 1px solid rgba(6, 182, 212, 0.4); }
.icon-sentira { background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(147, 51, 234, 0.25)); border: 1px solid rgba(59, 130, 246, 0.4); }

.card-badge {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-muted);
}

.card h2 {
  font-size: 1.55rem;
  font-weight: 700;
  margin-bottom: 0.65rem;
  letter-spacing: -0.02em;
}

.card p.desc {
  color: var(--text-muted);
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
  flex-grow: 1;
}

.feature-list {
  list-style: none;
  margin-bottom: 1.75rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-dim);
  margin-bottom: 0.45rem;
}

.feature-list li::before {
  content: "✓";
  color: #38bdf8;
  font-weight: 800;
}

.card-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.status {
  font-size: 0.78rem;
  font-weight: 600;
  color: #eab308;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.status::before {
  content: "";
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #eab308;
  box-shadow: 0 0 8px #eab308;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-gradient);
  color: white;
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  transition: all 0.25s ease;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35);
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(99, 102, 241, 0.55);
  color: white;
}

.disabled-pill {
  font-size: 0.84rem;
  color: var(--text-dim);
  padding: 0.6rem 0.9rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  text-align: center;
}

footer {
  margin-top: auto;
  padding: 2.5rem 0 3rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(7, 10, 19, 0.9);
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  text-align: center;
}

footer nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1.5rem;
}

footer a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s ease;
}

footer a:hover {
  color: #38bdf8;
}

.footer-note {
  font-size: 0.8rem;
  color: var(--text-dim);
  max-width: 600px;
}

.page-wrapper {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 18px;
  padding: 3rem 2.5rem;
  margin: 3rem 0;
  backdrop-filter: blur(16px);
}

.page-wrapper h1 {
  font-size: 2.2rem;
  font-weight: 800;
  margin-bottom: 1.25rem;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-wrapper p {
  color: var(--text-muted);
  font-size: 1.05rem;
  line-height: 1.7;
  margin-bottom: 1.25rem;
}

@media (max-width: 768px) {
  .hero h1 { font-size: 2.1rem; }
  .grid { grid-template-columns: 1fr; }
  .page-wrapper { padding: 2rem 1.5rem; }
}
"""


def _page(title: str, body: str) -> bytes:
    navigation = " ".join(
        f'<a href="{path}">{label}</a>'
        for path, label in (
            ("/", "Products"),
            ("/about", "About"),
            ("/contact", "Contact"),
            ("/terms", "Terms"),
            ("/privacy", "Privacy"),
            ("/user-policy", "User Policy"),
        )
    )
    logo_img = (
        f'<img class="brand-logo" src="data:image/png;base64,{_LOGO_B64}" alt="Gaatha Logo">'
        if _LOGO_B64
        else '<div class="brand-logo" style="background:var(--accent-gradient)"></div>'
    )
    favicon_link = (
        f'<link rel="icon" type="image/png" href="data:image/png;base64,{_LOGO_B64}">'
        if _LOGO_B64
        else ""
    )

    html_content = (
        '<!doctype html><html lang="en"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)} | GaathaCore</title>"
        f"{favicon_link}"
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
        f"<style>{CSS_STYLES}</style>"
        '</head><body>'
        '<header><div class="container header-content">'
        f'<a href="/" class="brand">{logo_img}<span class="brand-title">Gaatha</span></a>'
        '<div class="badge-tag">Unified Apex Platform</div>'
        '</div></header>'
        f'<main class="container">{body}</main>'
        '<footer><div class="container footer-content">'
        f'<nav aria-label="Public pages">{navigation}</nav>'
        '<p class="footer-note">GaathaCore does not display service health or internal deployment details on this public page. Product access is sovereign and mediated exclusively through native product authentication boundaries.</p>'
        '<p class="footer-note" style="color:rgba(255,255,255,0.2);font-size:0.72rem;">&copy; 2026 Gaatha. All product rights reserved.</p>'
        '</div></footer>'
        '</body></html>'
    )
    return html_content.encode("utf-8")


PRODUCT_METADATA = {
    "suite": {
        "icon": "📊",
        "icon_class": "icon-suite",
        "category": "Enterprise Cloud ERP",
        "features": [
            "Multi-Entity Chart of Accounts & Journals",
            "GST, VAT, & Automated Client Invoicing",
            "CRM Deals & Lead Pipelines",
            "HRM, Attendance & Employee Management",
            "Real-Time Executive BI Reports",
        ],
    },
    "pos": {
        "icon": "⚡",
        "icon_class": "icon-pos",
        "category": "Smart Restaurant & Retail",
        "features": [
            "Ultra-Fast Order & Floor Management",
            "Live Kitchen Display System (KDS)",
            "Dynamic Bill Splitting & Multi-Payment",
            "Real-Time Recipe & Stock Deduction",
            "Offline-Resilient Cloud Architecture",
        ],
    },
    "sentira": {
        "icon": "👁️",
        "icon_class": "icon-sentira",
        "category": "Visual AI & CCTV Surveillance",
        "features": [
            "Sub-Second Low-Latency Video Streaming",
            "Intelligent Edge Threat & Event Detection",
            "Multi-Tenant Site & Camera Governance",
            "Tamper-Evident Media Evidence Vault",
            "Granular Role & Stream Access Permissions",
        ],
    },
}


def render_home(products: Iterable[PublicProduct]) -> bytes:
    cards = []
    for product in products:
        meta = PRODUCT_METADATA.get(
            product.policy.key,
            {
                "icon": "🚀",
                "icon_class": "icon-suite",
                "category": "Cloud Service",
                "features": ["Verified multi-tenant architecture"],
            },
        )
        link = (
            f'<a class="button" href="{html.escape(product.entry_url, quote=True)}">Open product</a>'
            if product.entry_url
            else '<p class="disabled-pill">Public entry is not available.</p>'
        )
        feature_items = "".join(f"<li>{html.escape(feat)}</li>" for feat in meta["features"])
        cards.append(
            f'<article class="card">'
            f'<div class="card-top">'
            f'<div class="product-icon-wrap {meta["icon_class"]}">{meta["icon"]}</div>'
            f'<span class="card-badge">{meta["category"]}</span>'
            f'</div>'
            f'<h2>{html.escape(product.name)}</h2>'
            f'<p class="desc">{html.escape(product.description)}</p>'
            f'<ul class="feature-list">{feature_items}</ul>'
            f'<div class="card-footer">'
            f'<p class="status">{html.escape(product.status)}</p>'
            f'{link}'
            f'</div>'
            f'</article>'
        )

    hero_html = (
        '<section class="hero">'
        '<div class="badge-tag" style="margin-bottom:1.25rem;">Enterprise Cloud Ecosystem</div>'
        '<h1>Gaatha <span class="hero-gradient">products</span></h1>'
        '<p>Public entry is enabled only after explicit policy approval and deployment validation. This directory does not make a product availability claim.</p>'
        '<div class="features-banner">'
        '<div class="feat-item"><span class="feat-dot"></span> Sovereign Databases</div>'
        '<div class="feat-item"><span class="feat-dot"></span> Strict RBAC Isolation</div>'
        '<div class="feat-item"><span class="feat-dot"></span> Zero Public DB Ports</div>'
        '<div class="feat-item"><span class="feat-dot"></span> Unified TLS Gateway</div>'
        '</div>'
        '</section>'
        f'<section class="grid">{"".join(cards)}</section>'
    )
    return _page("Products", hero_html)


def public_entry_app(environ: dict[str, str], start_response: Callable) -> list[bytes]:
    path = environ.get("PATH_INFO", "/")
    if path == "/healthz":
        start_response("200 OK", [("Content-Type", "application/json"), ("Cache-Control", "no-store")])
        return [b'{"status":"available"}']
    if path not in PUBLIC_PATHS:
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not found"]
    content = {
        "/about": (
            "About",
            '<div class="page-wrapper">'
            '<h1>About GaathaCore</h1>'
            '<p>GaathaCore provides a unified, hardened public starting point while each underlying application retains sovereign services, isolated PostgreSQL databases, and distinct authorization boundaries.</p>'
            '<p>Our ecosystem unites mission-critical enterprise workflows: <strong>Gaatha Suite</strong> for enterprise resource planning, <strong>Gaatha POS</strong> for point-of-sale restaurant and retail management, and <strong>Sentira</strong> for next-generation visual intelligence and security.</p>'
            '</div>',
        ),
        "/contact": (
            "Contact",
            '<div class="page-wrapper">'
            '<h1>Contact Support</h1>'
            '<p>Use the designated support or administrator channel provided by your organization.</p>'
            '<p>For administrative or infrastructure inquiries, reach out to your account administrator or primary organization support team.</p>'
            '</div>',
        ),
        "/terms": (
            "Terms",
            '<div class="page-wrapper">'
            '<h1>Terms of Service</h1>'
            '<p>Product terms are provided by the relevant product where available.</p>'
            '<p>Access to individual services is conditioned upon acceptable organization use policies and verified credential ownership.</p>'
            '</div>',
        ),
        "/privacy": (
            "Privacy",
            '<div class="page-wrapper">'
            '<h1>Privacy Policy</h1>'
            '<p>Privacy information is provided by the relevant product where available.</p>'
            '<p>Tenant data is strictly partitioned across sovereign database clusters with zero cross-tenant querying or shared data access.</p>'
            '</div>',
        ),
        "/user-policy": (
            "User Policy",
            '<div class="page-wrapper">'
            '<h1>User Access Policy</h1>'
            '<p>Use only the product access assigned to you and do not attempt to bypass authentication or authorization controls.</p>'
            '<p>All administrative mutations and access events are recorded in immutable audit logs.</p>'
            '</div>',
        ),
    }
    payload = render_home(configured_products(environ)) if path == "/" else _page(*content[path])
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ],
    )
    return [payload]
