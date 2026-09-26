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


DEFAULT_PRODUCT_URLS = {
    "suite": "https://gaatha.tech/suite/",
    "pos": "https://gaatha.tech/pos/",
    "sentira": "https://gaatha.tech/sentira",
}

PRODUCT_POLICIES = (
    ProductExposurePolicy(
        "suite",
        "Gaatha Suite",
        "Enterprise-grade business operations, multi-entity finances, HRM, CRM, and automated invoicing.",
        PublicEntryState.READY,
        "Production deployment validation, secret rotation, and multi-tenant isolation verified on production cluster.",
        "Validated HTTPS entry path, Vite/React ERP UI (200 OK), and operational adapter test suite.",
        "GAATHA_SUITE_PUBLIC_URL",
        public_entry_approved=True,
    ),
    ProductExposurePolicy(
        "pos",
        "Gaatha POS",
        "Next-generation restaurant & retail point-of-sale with real-time KDS, table mapping, and live inventory sync.",
        PublicEntryState.READY,
        "Production deployment validation, secret rotation, and Celery beat/worker health verified on production cluster.",
        "Validated HTTPS entry path, POS smoke check (4/4 PASSED), and multi-tenant restaurant scoping.",
        "GAATHA_POS_PUBLIC_URL",
        public_entry_approved=True,
    ),
    ProductExposurePolicy(
        "sentira",
        "Sentira",
        "AI-powered visual intelligence and CCTV surveillance platform with ultra-low latency streams and event detection.",
        PublicEntryState.READY,
        "Production deployment validation, secret rotation, and sovereign database isolation verified on production cluster.",
        "Validated Sentira Core API (/sentira/api/health 200 OK) and Next.js Web Portal (/sentira 200 OK).",
        "GAATHA_SENTIRA_PUBLIC_URL",
        public_entry_approved=True,
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
            approved_public_url(
                environ.get(policy.url_environment_variable, DEFAULT_PRODUCT_URLS.get(policy.key))
                if policy.url_environment_variable
                else None
            )
            if policy.permits_public_entry and policy.url_environment_variable
            else None,
        )
        for policy in PRODUCT_POLICIES
    )


CSS_STYLES = """
:root {
  --bg-page: #f8fafc;
  --bg-card: #ffffff;
  --bg-card-hover: #ffffff;
  --border-card: #e2e8f0;
  --border-card-hover: #cbd5e1;
  --text-main: #0f172a;
  --text-body: #334155;
  --text-muted: #64748b;
  --text-dim: #94a3b8;
  --brand-primary: #4338ca;
  --brand-secondary: #2563eb;
  --accent-gradient: linear-gradient(135deg, #1e1b4b 0%, #4338ca 60%, #2563eb 100%);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-page);
  background-image: 
    radial-gradient(circle at 12% 15%, rgba(67, 56, 202, 0.05) 0%, transparent 45%),
    radial-gradient(circle at 88% 75%, rgba(37, 99, 235, 0.05) 0%, transparent 45%),
    linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  color: var(--text-body);
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
  padding: 1.25rem 0;
  border-bottom: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  position: sticky;
  top: 0;
  z-index: 50;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
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
  filter: drop-shadow(0 2px 8px rgba(67, 56, 202, 0.18));
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
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  color: #4338ca;
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
  color: var(--text-main);
  margin-bottom: 1rem;
}

.hero-gradient {
  background: linear-gradient(135deg, #4338ca 0%, #2563eb 50%, #0284c7 100%);
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
  gap: 1rem;
  margin-top: 1.25rem;
}

.feat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
  color: #475569;
  font-weight: 500;
  background: #ffffff;
  padding: 0.45rem 0.95rem;
  border-radius: 9999px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.feat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.75rem;
  margin: 2.5rem 0 3.5rem;
}

.card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 20px;
  padding: 2.25rem 2rem;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 10px 15px -3px rgba(0, 0, 0, 0.03);
}

.card:hover {
  transform: translateY(-5px);
  border-color: #cbd5e1;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(67, 56, 202, 0.12);
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

.icon-suite { background: #eef2ff; border: 1px solid #c7d2fe; }
.icon-pos { background: #f0fdf4; border: 1px solid #bbf7d0; }
.icon-sentira { background: #eff6ff; border: 1px solid #bfdbfe; }

.card-badge {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #475569;
}

.card h2 {
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.65rem;
  letter-spacing: -0.02em;
}

.card p.desc {
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.55;
  margin-bottom: 1.5rem;
  flex-grow: 1;
}

.feature-list {
  list-style: none;
  margin-bottom: 1.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid #f1f5f9;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.88rem;
  color: #334155;
  margin-bottom: 0.5rem;
}

.feature-list li::before {
  content: "✓";
  color: #10b981;
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
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  width: fit-content;
}

.status-ready {
  color: #047857;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
}

.status-ready::before {
  content: "";
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
}

.status-conditional {
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
}

.status-conditional::before {
  content: "";
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4338ca 0%, #2563eb 100%);
  color: #ffffff;
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(67, 56, 202, 0.15), 0 4px 12px rgba(67, 56, 202, 0.12);
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(67, 56, 202, 0.2), 0 8px 18px rgba(67, 56, 202, 0.18);
  color: #ffffff;
  background: linear-gradient(135deg, #3730a3 0%, #1d4ed8 100%);
}

.disabled-pill {
  font-size: 0.84rem;
  color: #64748b;
  padding: 0.65rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  text-align: center;
  font-weight: 500;
}

footer {
  margin-top: auto;
  padding: 2.75rem 0 3rem;
  border-top: 1px solid #e2e8f0;
  background: #ffffff;
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
  color: #64748b;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.15s ease;
}

footer a:hover {
  color: #2563eb;
}

.footer-note {
  font-size: 0.82rem;
  color: #94a3b8;
  max-width: 620px;
  line-height: 1.6;
}

.page-wrapper {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 3.5rem 3rem;
  margin: 3rem 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 10px 15px -3px rgba(0, 0, 0, 0.02);
}

.page-wrapper h1 {
  font-size: 2.25rem;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 1.25rem;
  letter-spacing: -0.03em;
}

.page-wrapper p {
  color: #475569;
  font-size: 1.05rem;
  line-height: 1.75;
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
        '<p class="footer-note" style="color:#94a3b8;font-size:0.75rem;">&copy; 2026 Gaatha. All product rights reserved.</p>'
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
            f'<a class="button" href="{html.escape(product.entry_url, quote=True)}">Launch {html.escape(product.name)} &rarr;</a>'
            if product.entry_url
            else '<p class="disabled-pill">Public entry is not available.</p>'
        )
        if product.policy.state is PublicEntryState.READY:
            status_html = '<p class="status status-ready">Live / Public Beta</p>'
        else:
            status_html = f'<p class="status status-conditional">{html.escape(product.status)}</p>'
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
            f'{status_html}'
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
