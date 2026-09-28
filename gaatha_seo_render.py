"""
GaathaCore SEO & Content Rendering Engine
Operated by GAATHA Ventures Sh.P.K. (NIPT: M62118505B), Durana Tech Park, Tirana, Albania.
"""

import html
import json
from typing import Optional
from urllib.parse import quote
import gaatha_blog_data as gbd

def build_breadcrumbs_json_ld(crumbs: list[tuple[str, str]]) -> str:
    """Builds Schema.org BreadcrumbList JSON-LD."""
    elements = []
    for i, (name, url) in enumerate(crumbs, 1):
        elements.append({
            "@type": "ListItem",
            "position": i,
            "name": name,
            "item": f"https://gaatha.tech{url}" if url.startswith("/") else url
        })
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements
    })

def build_article_json_ld(article: dict) -> str:
    """Builds Schema.org Article JSON-LD."""
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article["title"],
        "description": article["seo_description"],
        "datePublished": article["published_date"],
        "dateModified": article["updated_date"],
        "author": {
            "@type": "Organization",
            "name": article["author"]["name"],
            "url": "https://gaatha.tech/"
        },
        "publisher": {
            "@type": "Organization",
            "name": "GAATHA Ventures Sh.P.K.",
            "url": "https://gaatha.tech/",
            "logo": {
                "@type": "ImageObject",
                "url": "https://gaatha.tech/logo.png"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"https://gaatha.tech/blog/{article['slug']}"
        }
    })

def render_solution_business_management() -> tuple[str, str, str, str]:
    """Returns (title, body, meta_description, extra_head)."""
    title = "SME Business Management & Cloud ERP Solutions"
    meta_desc = "Unified business management software for growing SMEs: double-entry bookkeeping, automated client invoicing, CRM pipeline tracking, and inventory governance."
    crumbs = [("Home", "/"), ("Solutions", "/solutions/business-management"), ("Business Management", "/solutions/business-management")]
    extra_head = f'<script type="application/ld+json">{build_breadcrumbs_json_ld(crumbs)}</script>'
    
    body = """
<div class="page-wrapper">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a> / <a href="/solutions/business-management">Solutions</a> / <span>Business Management</span>
    </nav>
    <div class="badge-tag mb-3">Enterprise Cloud ERP</div>
    <h1>Business Management & Operations for Growing SMEs</h1>
    <p class="lead">Eliminate disconnected spreadsheets and fragmented accounting with a unified, sovereign enterprise platform built for operational control and statutory compliance.</p>
    <hr style="border-color:var(--border-card);margin:1.5rem 0;">
    
    <div class="solution-grid">
        <div class="solution-card">
            <div class="solution-icon">📊</div>
            <h3>Financial Governance & Ledgers</h3>
            <p>Enforce double-entry accounting integrity across multi-entity journals, automated VAT/tax calculations, and real-time bank reconciliation.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">💼</div>
            <h3>Commercial CRM Pipelines</h3>
            <p>Track prospective deals from initial inquiry to signed contract, with automatic quotation-to-invoice conversion.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">📦</div>
            <h3>Inventory & Warehouse Control</h3>
            <p>Maintain precise stock balances with automated reorder triggers, FIFO valuation, and multi-location governance.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">👥</div>
            <h3>Human Capital & Payroll</h3>
            <p>Centrally manage employee attendance, leave allocations, and payroll disbursements within a hardened authorization perimeter.</p>
        </div>
    </div>
    
    <div class="cta-banner mt-5">
        <div>
            <h3>Experience Gaatha Suite</h3>
            <p>Explore sovereign enterprise cloud ERP designed for modern European and international businesses.</p>
        </div>
        <a href="/suite" class="btn-primary">Access Gaatha Suite</a>
    </div>

    <div class="related-section mt-5">
        <h3>Related Educational Insights</h3>
        <ul>
            <li><a href="/blog/how-to-choose-business-management-software-sme">How to Choose Business Management Software for a Growing SME</a></li>
            <li><a href="/blog/erp-vs-crm-understanding-the-difference">ERP vs CRM: Understanding the Difference and When You Need Both</a></li>
            <li><a href="/blog/business-automation-for-small-and-medium-businesses">Business Automation for Small and Medium Businesses: Practical Workflows</a></li>
        </ul>
    </div>
</div>
"""
    return title, body, meta_desc, extra_head

def render_solution_restaurant_pos() -> tuple[str, str, str, str]:
    title = "Modern Restaurant POS & Kitchen Operations"
    meta_desc = "High-performance restaurant point-of-sale software: Kitchen Display Systems (KDS), visual floor plans, recipe-level stock depletion, and fast split billing."
    crumbs = [("Home", "/"), ("Solutions", "/solutions/restaurant-pos"), ("Restaurant POS", "/solutions/restaurant-pos")]
    extra_head = f'<script type="application/ld+json">{build_breadcrumbs_json_ld(crumbs)}</script>'

    body = """
<div class="page-wrapper">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a> / <a href="/solutions/restaurant-pos">Solutions</a> / <span>Restaurant POS</span>
    </nav>
    <div class="badge-tag mb-3">Hospitality Technology</div>
    <h1>Restaurant Point of Sale & Kitchen Management</h1>
    <p class="lead">Accelerate service speed, eliminate order errors, and protect thin dining margins with an integrated, high-velocity restaurant operating system.</p>
    <hr style="border-color:var(--border-card);margin:1.5rem 0;">
    
    <div class="solution-grid">
        <div class="solution-card">
            <div class="solution-icon">⚡</div>
            <h3>Multi-Register Order Processing</h3>
            <p>Fast, tactile order entry with modifier options, combo pricing, and table-side handheld terminal support.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">🍳</div>
            <h3>Kitchen Display Systems (KDS)</h3>
            <p>Route orders to hot, cold, and beverage stations instantly with elapsed preparation timing and color-coded rush flags.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">🥗</div>
            <h3>Recipe-Level Ingredient Depletion</h3>
            <p>Deduct raw ingredients automatically with every dish sold to identify kitchen waste, portion drift, and food cost variances.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">💳</div>
            <h3>Split Payments & Settlement</h3>
            <p>Effortlessly split bills by seat, item, or exact amount to avoid queue delays during peak checkout rushes.</p>
        </div>
    </div>
    
    <div class="cta-banner mt-5">
        <div>
            <h3>Explore Gaatha POS</h3>
            <p>Deploy dependable, cloud-synchronized point-of-sale hardware and software for your restaurant or cafe.</p>
        </div>
        <a href="/pos" class="btn-primary">Access Gaatha POS</a>
    </div>

    <div class="related-section mt-5">
        <h3>Related Hospitality Insights</h3>
        <ul>
            <li><a href="/blog/how-modern-pos-software-helps-restaurants">How Modern POS Software Helps Restaurants Streamline Daily Operations</a></li>
            <li><a href="/blog/restaurant-inventory-management-practical-guide">Restaurant Inventory Management: A Practical Guide to Waste Reduction</a></li>
            <li><a href="/blog/what-should-modern-restaurant-pos-track">What Should a Modern Restaurant POS System Track? Core Metrics That Matter</a></li>
        </ul>
    </div>
</div>
"""
    return title, body, meta_desc, extra_head

def render_solution_ai_video_analytics() -> tuple[str, str, str, str]:
    title = "AI Video Analytics & Visual Perimeter Security"
    meta_desc = "Transform passive CCTV cameras into real-time security intelligence: perimeter tripwires, unattended object detection, and privacy-compliant edge inference."
    crumbs = [("Home", "/"), ("Solutions", "/solutions/ai-video-analytics"), ("AI Video Analytics", "/solutions/ai-video-analytics")]
    extra_head = f'<script type="application/ld+json">{build_breadcrumbs_json_ld(crumbs)}</script>'

    body = """
<div class="page-wrapper">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a> / <a href="/solutions/ai-video-analytics">Solutions</a> / <span>AI Video Analytics</span>
    </nav>
    <div class="badge-tag mb-3">Computer Vision Intelligence</div>
    <h1>AI Video Analytics & Perimeter Intelligence</h1>
    <p class="lead">Convert passive RTSP/ONVIF security cameras into proactive event awareness systems without compromising European data privacy standards.</p>
    <hr style="border-color:var(--border-card);margin:1.5rem 0;">
    
    <div class="solution-grid">
        <div class="solution-card">
            <div class="solution-icon">👁️</div>
            <h3>Real-Time Stream Ingestion</h3>
            <p>Sub-second low-latency RTSP video processing compatible with standard commercial security camera networks.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">🚨</div>
            <h3>Rule-Based Perimeter Tripwires</h3>
            <p>Automated alerts for unauthorized intrusion, restricted zone crossing, and after-hours property boundary breaches.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">🔒</div>
            <h3>Privacy-Preserving Edge Architecture</h3>
            <p>On-premises inference keeps high-resolution raw video secure on-site, transmitting only structured alert telemetry.</p>
        </div>
        <div class="solution-card">
            <div class="solution-icon">🛡️</div>
            <h3>Human-in-the-Loop Governance</h3>
            <p>Automated detections act as assistive notifications for human security staff, adhering to strict ethical oversight standards.</p>
        </div>
    </div>
    
    <div class="cta-banner mt-5">
        <div>
            <h3>Discover Sentira Visual AI</h3>
            <p>Connect your camera feeds to an intelligent, multi-tenant visual awareness dashboard.</p>
        </div>
        <a href="/sentira" class="btn-primary">Access Sentira</a>
    </div>

    <div class="related-section mt-5">
        <h3>Related Intelligence Guides</h3>
        <ul>
            <li><a href="/blog/ai-video-analytics-for-business-security">AI Video Analytics for Business Security: What Businesses Should Know</a></li>
            <li><a href="/blog/how-ai-can-support-business-operations">How AI Can Support Business Operations Without Replacing Human Decision-Making</a></li>
        </ul>
    </div>
</div>
"""
    return title, body, meta_desc, extra_head

def render_blog_index(category_slug: Optional[str] = None, search_query: str = "") -> tuple[str, str, str, str]:
    posts = gbd.get_all_posts()
    current_cat_name = None
    if category_slug:
        cat_obj = gbd.get_category_by_slug(category_slug)
        if cat_obj:
            current_cat_name = cat_obj["name"]
            posts = [p for p in posts if p["category_slug"] == category_slug]
    if search_query:
        q = search_query.lower()
        posts = [p for p in posts if q in p["title"].lower() or q in p["excerpt"].lower()]

    title = f"{current_cat_name} Articles" if current_cat_name else "Insights & Enterprise Knowledge"
    meta_desc = "Authoritative research, operational frameworks, and practical guides on SME ERP, modern restaurant POS, and AI video analytics."
    crumbs = [("Home", "/"), ("Insights & Blog", "/blog")]
    if current_cat_name and category_slug:
        crumbs.append((current_cat_name, f"/blog/category/{category_slug}"))
    extra_head = f'<script type="application/ld+json">{build_breadcrumbs_json_ld(crumbs)}</script>'

    # Categories pills
    cat_pills = []
    all_active = "active" if not category_slug else ""
    cat_pills.append(f'<a href="/blog" class="cat-pill {all_active}">All Articles ({len(gbd.get_all_posts())})</a>')
    for c in gbd.get_categories():
        active = "active" if category_slug == c["slug"] else ""
        cat_pills.append(f'<a href="/blog/category/{c["slug"]}" class="cat-pill {active}">{html.escape(c["name"])} ({c["count"]})</a>')

    # Post cards
    cards = []
    for p in posts:
        cards.append(f"""
        <article class="blog-card">
            <div class="blog-card-meta">
                <span class="badge-tag">{html.escape(p["category"])}</span>
                <span class="reading-time">⏱️ {p["reading_time"]}</span>
            </div>
            <h2><a href="/blog/{p["slug"]}">{html.escape(p["title"])}</a></h2>
            <p class="blog-excerpt">{html.escape(p["excerpt"])}</p>
            <div class="blog-footer-meta">
                <span>By {html.escape(p["author"]["name"])}</span>
                <span>{p["published_date"]}</span>
            </div>
        </article>
        """)

    cards_html = "".join(cards) if cards else '<p class="text-muted">No articles found matching your criteria.</p>'

    body = f"""
<div class="page-wrapper">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a> / <span>Insights & Blog</span>
    </nav>
    <div class="badge-tag mb-3">Knowledge Base & Research</div>
    <h1>GaathaCore <span class="hero-gradient">Insights</span></h1>
    <p class="lead">Actionable, vendor-neutral research on SME operational management, point-of-sale systems, and ethical computer vision intelligence. Authored by GAATHA Ventures Sh.P.K.</p>
    
    <div class="cat-pills-bar mt-4 mb-4">
        {' '.join(cat_pills)}
    </div>

    <div class="blog-grid">
        {cards_html}
    </div>

    <div class="trust-box mt-5">
        <h4>Editorial Transparency & Authorship Notice</h4>
        <p>Published by <strong>GAATHA Ventures Sh.P.K.</strong> (NIPT: <code>M62118505B</code>), Durana Tech Park, Albania. Our editorial content is strictly fact-checked and designed to provide educational clarity on business software architectures, operational workflows, and data protection compliance.</p>
    </div>
</div>
"""
    return title, body, meta_desc, extra_head

def render_blog_article(slug: str) -> Optional[tuple[str, str, str, str]]:
    article = gbd.get_post_by_slug(slug)
    if not article:
        return None

    title = article["title"]
    meta_desc = article["seo_description"]
    crumbs = [
        ("Home", "/"),
        ("Insights & Blog", "/blog"),
        (article["category"], f"/blog/category/{article['category_slug']}"),
        (article["title"], f"/blog/{article['slug']}")
    ]
    extra_head = (
        f'<script type="application/ld+json">{build_breadcrumbs_json_ld(crumbs)}</script>\n'
        f'<script type="application/ld+json">{build_article_json_ld(article)}</script>'
    )

    # Table of contents
    toc_items = "".join(
        f'<li><a href="#{item["id"]}">{html.escape(item["title"])}</a></li>'
        for item in article.get("table_of_contents", [])
    )
    toc_html = f"""
    <div class="toc-box">
        <div class="toc-title">Table of Contents</div>
        <ul>{toc_items}</ul>
    </div>
    """ if toc_items else ""

    # Related articles
    related = gbd.get_related_posts(slug, limit=3)
    rel_cards = "".join(f"""
    <div class="related-card">
        <span class="badge-tag">{html.escape(r["category"])}</span>
        <h4><a href="/blog/{r["slug"]}">{html.escape(r["title"])}</a></h4>
        <span class="reading-time">⏱️ {r["reading_time"]}</span>
    </div>
    """ for r in related)

    body = f"""
<div class="article-wrapper">
    <nav class="breadcrumb-nav">
        <a href="/">Home</a> / <a href="/blog">Insights</a> / <a href="/blog/category/{article['category_slug']}">{html.escape(article['category'])}</a> / <span>{html.escape(article['title'])}</span>
    </nav>
    <div class="badge-tag mb-3">{html.escape(article["category"])}</div>
    <h1 class="article-title">{html.escape(article["title"])}</h1>
    
    <div class="article-meta-bar">
        <span><i class="icon">✍️</i> By <strong>{html.escape(article["author"]["name"])}</strong> ({article["author"]["role"]})</span>
        <span><i class="icon">📅</i> Published: {article["published_date"]}</span>
        <span><i class="icon">🔄</i> Last Reviewed: {article["updated_date"]}</span>
        <span><i class="icon">⏱️</i> {article["reading_time"]}</span>
    </div>

    {toc_html}

    <div class="article-body">
        {article["content_html"]}
    </div>

    <div class="disclaimer-card mt-5">
        <strong>Editorial Notice & Transparency:</strong>
        <p class="mb-0 mt-1">This article is published for general educational and informational purposes by GAATHA Ventures Sh.P.K. While based on verified operational engineering practices, business requirements differ across jurisdictions and industries. Consult qualified financial, tax, or legal advisors for specific enterprise implementations.</p>
    </div>

    <div class="author-card mt-4">
        <div class="author-avatar">🏢</div>
        <div>
            <h4>{html.escape(article["author"]["name"])}</h4>
            <p class="author-role">{html.escape(article["author"]["role"])} &bull; {html.escape(article["author"]["entity"])}</p>
            <p class="author-desc">Dedicated research desk analyzing enterprise cloud software architectures, point-of-sale operational efficiency, and privacy-preserving computer vision technologies.</p>
        </div>
    </div>

    <div class="related-section mt-5">
        <h3>Related Operational Guides</h3>
        <div class="related-grid mt-3">
            {rel_cards}
        </div>
    </div>
</div>
"""
    return title, body, meta_desc, extra_head
