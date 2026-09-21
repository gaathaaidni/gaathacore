import os
import re
import pytest
import requests


DEPLOY_URL = os.environ.get("DEPLOY_URL")
SUPERADMIN_USER = os.environ.get("SUPERADMIN_USER", "superadmin")
SUPERADMIN_PASS = os.environ.get("SUPERADMIN_PASS", "superadmin@123")


@pytest.mark.skipif(not DEPLOY_URL, reason="DEPLOY_URL not set")
def test_deployed_site_core_pages():
    """Basic smoke checks against the deployed site. Skips when DEPLOY_URL not provided."""
    s = requests.Session()

    def get_csrf(token_url):
        r = s.get(token_url, timeout=10)
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', r.text)
        return m.group(1) if m else None

    # Check root
    r = s.get(DEPLOY_URL, timeout=10)
    assert r.status_code in (200, 302), f"Root returned {r.status_code}"

    # Login as superadmin
    login_csrf = get_csrf(f"{DEPLOY_URL}/auth/login")
    payload = {"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS}
    if login_csrf:
        payload["csrf_token"] = login_csrf

    r = s.post(f"{DEPLOY_URL}/auth/login", data=payload, allow_redirects=True, timeout=10)
    assert r.status_code in (200, 302), f"Login attempt returned {r.status_code}"

    # Check admin dashboard
    r = s.get(f"{DEPLOY_URL}/admin/", allow_redirects=True, timeout=10)
    assert r.status_code in (200, 302), f"Admin dashboard returned {r.status_code}"

    # Check POS page
    r = s.get(f"{DEPLOY_URL}/pos/", allow_redirects=True, timeout=10)
    assert r.status_code in (200, 302), f"POS page returned {r.status_code}"

    # Check KDS orders API
    r = s.get(f"{DEPLOY_URL}/kds/orders", timeout=10)
    assert r.status_code in (200, 401, 403), f"KDS orders returned {r.status_code}"

    # Check admin API endpoints (users, menu, collections)
    for ep in ("/admin/api/users", "/admin/api/menu", "/admin/api/collections"):
        r = s.get(DEPLOY_URL + ep, allow_redirects=True, timeout=10)
        assert r.status_code in (200, 302, 403), f"{ep} returned {r.status_code}"
