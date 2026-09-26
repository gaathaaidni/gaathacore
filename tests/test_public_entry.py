from public_entry import (
    PRODUCT_POLICIES,
    PUBLIC_ENTRY_HOST,
    PublicEntryState,
    ProductExposurePolicy,
    PublicProduct,
    approved_public_url,
    configured_products,
    public_entry_app,
)


def response(path="/", environ=None):
    captured = {}
    result = public_entry_app({"PATH_INFO": path, **(environ or {})}, lambda status, headers: captured.update(status=status, headers=headers))
    return captured, b"".join(result).decode()


def test_catalog_contains_only_the_three_public_scope_products_with_explicit_policy_fields():
    assert PUBLIC_ENTRY_HOST == "gaatha.tech"
    assert [policy.key for policy in PRODUCT_POLICIES] == ["suite", "pos", "sentira"]
    assert [product.name for product in configured_products({})] == ["Gaatha Suite", "Gaatha POS", "Sentira"]
    assert all(policy.reason and policy.required_deployment_validation for policy in PRODUCT_POLICIES)
    assert all(policy.permits_public_entry for policy in PRODUCT_POLICIES)
    _, body = response()
    assert "Launch Gaatha Suite" in body and "Launch Gaatha POS" in body and "Launch Sentira" in body
    assert "https://gaatha.tech/suite/" in body
    assert "https://gaatha.tech/pos/" in body
    assert "https://gaatha.tech/sentira" in body
    assert "Phoenix" not in body and "Gaatha AI" not in body and "Gaatha Terra" not in body and "PostPilot" not in body


def test_postpilot_is_not_catalogued_or_exposed_even_if_an_environment_url_is_set():
    products = configured_products({"GAATHA_POSTPILOT_PUBLIC_URL": "https://gaatha.tech/postpilot"})
    assert all(product.policy.key != "postpilot" for product in products)
    _, body = response(environ={"GAATHA_POSTPILOT_PUBLIC_URL": "https://gaatha.tech/postpilot"})
    assert "PostPilot" not in body and "https://gaatha.tech/postpilot" not in body


def test_unapproved_urls_are_rejected_and_never_leak_to_the_page():
    for value in ("http://gaatha.tech/suite", "https://app.gaatha.tech/suite", "https://localhost/suite", "https://192.168.1.10/suite", "https://internal/suite", "https://user:pass@gaatha.tech/suite"):
        assert approved_public_url(value) is None
    _, body = response(environ={"GAATHA_SUITE_PUBLIC_URL": "http://internal:3000", "GAATHA_POS_PUBLIC_URL": "https://other.gaatha.tech/pos"})
    assert "internal:3000" not in body and "other.gaatha.tech" not in body


def test_conditional_products_cannot_bypass_policy_with_a_configured_url():
    conditional_policy = ProductExposurePolicy(
        "test_gated", "Test Gated", "Desc", PublicEntryState.CONDITIONAL, "reason", "val", "GAATHA_TEST_URL", public_entry_approved=False
    )
    assert not conditional_policy.permits_public_entry
    prod = PublicProduct(conditional_policy, approved_public_url("https://gaatha.tech/test") if conditional_policy.permits_public_entry else None)
    assert prod.entry_url is None


def test_ready_state_requires_explicit_policy_approval():
    unapproved = ProductExposurePolicy("test", "Test", "Test", PublicEntryState.READY, "reason", "validation", "GAATHA_TEST_PUBLIC_URL")
    approved = ProductExposurePolicy("test", "Test", "Test", PublicEntryState.READY, "reason", "validation", "GAATHA_TEST_PUBLIC_URL", public_entry_approved=True)
    assert not unapproved.permits_public_entry
    assert approved.permits_public_entry


def test_public_routes_are_safe_and_health_does_not_disclose_dependencies():
    captured, health = response("/healthz")
    assert captured["status"] == "200 OK"
    assert health == '{"status":"available"}'
    captured, body = response("/missing")
    assert captured["status"] == "404 Not Found"
    assert body == "Not found"
