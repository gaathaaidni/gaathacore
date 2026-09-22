"""A dependency-free, fail-closed public entry page for GaathaCore.

This module deliberately does not probe or proxy product services.  A product
link is only rendered after an operator supplies an approved public HTTPS URL;
otherwise the page makes the unavailable/not-connected state explicit.
"""
from __future__ import annotations

import html
import os
from dataclasses import dataclass
from typing import Callable, Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class PublicProduct:
    name: str
    description: str
    entry_url: str | None

    @property
    def status(self) -> str:
        return "Entry configured" if self.entry_url else "Not yet connected"


PRODUCTS = (
    ("Gaatha Suite", "Business-management tools for organization operations.", "SUITE"),
    ("Gaatha POS", "Restaurant point-of-sale tools for day-to-day operations.", "POS"),
    ("Sentira", "Visual monitoring and event-awareness tools for authorized teams.", "SENTIRA"),
    ("PostPilot", "Content publishing workflow tools for authorized teams.", "POSTPILOT"),
)
PUBLIC_PATHS = {"/", "/about", "/contact", "/terms", "/privacy", "/user-policy", "/healthz"}


def approved_public_url(value: str | None) -> str | None:
    """Accept only an explicit HTTPS public URL, never a local/internal URL."""
    if not value:
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    # The launch surface is explicitly app.gaatha.tech. Limiting entries to this
    # host prevents an environment value from publishing an internal endpoint.
    if parsed.hostname.lower() != "app.gaatha.tech":
        return None
    return value.strip()


def configured_products(environ: dict[str, str] | None = None) -> tuple[PublicProduct, ...]:
    environ = os.environ if environ is None else environ
    return tuple(
        PublicProduct(name, description, approved_public_url(environ.get(f"GAATHA_{key}_PUBLIC_URL")))
        for name, description, key in PRODUCTS
    )


def _page(title: str, body: str) -> bytes:
    navigation = " ".join(f'<a href="{path}">{label}</a>' for path, label in (
        ("/", "Products"), ("/about", "About"), ("/contact", "Contact"),
        ("/terms", "Terms"), ("/privacy", "Privacy"), ("/user-policy", "User Policy"),
    ))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)} | GaathaCore</title><style>body{{font-family:system-ui,sans-serif;max-width:960px;margin:auto;padding:2rem;color:#172033;background:#f7f9fc}}header,footer{{padding:1rem 0}}a{{color:#1557a6}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem}}article{{background:white;border:1px solid #d8e0eb;border-radius:12px;padding:1.25rem}}.status{{font-weight:600;color:#4f3b00}}.button{{display:inline-block;background:#1557a6;color:white;padding:.65rem .9rem;border-radius:6px;text-decoration:none}}</style></head><body><header><strong>GaathaCore</strong><p>One public starting point for Gaatha products. Product access remains controlled by each product's own authentication and authorization boundary.</p></header><main>{body}</main><footer><nav aria-label="Public pages">{navigation}</nav><p>GaathaCore does not display service health or internal deployment details on this public page.</p></footer></body></html>""".encode("utf-8")


def render_home(products: Iterable[PublicProduct]) -> bytes:
    cards = []
    for product in products:
        link = f'<a class="button" href="{html.escape(product.entry_url, quote=True)}">Open product</a>' if product.entry_url else "<p>No public entry has been connected for this product.</p>"
        cards.append(f"<article><h2>{html.escape(product.name)}</h2><p>{html.escape(product.description)}</p><p class=\"status\">{product.status}</p>{link}</article>")
    return _page("Products", "<h1>Gaatha products</h1><p>Select a connected product entry. A configured link indicates only that an approved public entry URL is present; it is not a live service-health claim.</p><section class=\"grid\">" + "".join(cards) + "</section>")


def public_entry_app(environ: dict[str, str], start_response: Callable) -> list[bytes]:
    path = environ.get("PATH_INFO", "/")
    if path == "/healthz":
        start_response("200 OK", [("Content-Type", "application/json"), ("Cache-Control", "no-store")])
        return [b'{"status":"available"}']
    if path not in PUBLIC_PATHS:
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"Not found"]
    content = {
        "/about": ("About", "<h1>About GaathaCore</h1><p>GaathaCore provides a unified public starting point while products retain their independent services, data stores, and access controls.</p>"),
        "/contact": ("Contact", "<h1>Contact</h1><p>Contact and support channels are not configured here. Use the support or administrator channel provided by your organization.</p>"),
        "/terms": ("Terms", "<h1>Terms</h1><p>Product terms are provided by the relevant product where available. This entry page does not make additional legal claims.</p>"),
        "/privacy": ("Privacy", "<h1>Privacy</h1><p>Privacy information is provided by the relevant product where available. This entry page does not collect product data.</p>"),
        "/user-policy": ("User Policy", "<h1>User Policy</h1><p>Use only the product access assigned to you and do not attempt to bypass authentication or authorization controls.</p>"),
    }
    payload = render_home(configured_products(environ)) if path == "/" else _page(*content[path])
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")])
    return [payload]
