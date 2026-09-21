#!/usr/bin/env python3
"""Lightweight link checker for a deployed Nexora POS site.

Usage: DEPLOY_URL=https://your.site python scripts/link_check.py
"""
import os
import re
import sys
import requests
from urllib.parse import urljoin, urlparse

BASE = os.environ.get('DEPLOY_URL')
if not BASE:
    print('Set DEPLOY_URL environment variable to the site to check')
    sys.exit(2)

seen = set()
errors = []

session = requests.Session()

def extract_links(html):
    return set(re.findall(r'href=["\']([^"\']+)["\']', html))

queue = [BASE]

while queue:
    url = queue.pop(0)
    if url in seen:
        continue
    seen.add(url)
    try:
        r = session.get(url, timeout=10)
    except Exception as e:
        errors.append((url, str(e)))
        print(f"ERROR: {url} -> {e}")
        continue

    if r.status_code >= 400:
        errors.append((url, r.status_code))
        print(f"BROKEN: {url} -> {r.status_code}")
    else:
        print(f"OK: {url} -> {r.status_code}")

    # gather same-domain links
    for href in extract_links(r.text):
        if href.startswith('#'):
            continue
        parsed = urlparse(href)
        if parsed.scheme and parsed.netloc and parsed.netloc != urlparse(BASE).netloc:
            continue
        next_url = urljoin(url, href)
        if next_url not in seen and next_url.startswith(BASE):
            queue.append(next_url)

print('\nSummary:')
print(f'Total pages scanned: {len(seen)}')
print(f'Errors found: {len(errors)}')
if errors:
    for u, err in errors:
        print(f'- {u} -> {err}')
