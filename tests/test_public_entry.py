from public_entry import (
    PRODUCT_POLICIES,
    PublicEntryState,
    ProductExposurePolicy,
    approved_public_url,
    configured_products,
    public_entry_app,
)


def response(path="/", environ=None):
    captured = {}
    result = public_entry_app({"PATH_INFO": path, **(environ or {})}, lambda status, headers: captured.update(status=status, headers=headers))
    return captured, b"".join(result).decode()


def test_catalog_is_exactly_four_named_products_with_explicit_policy_fields():
    assert [policy.key for policy in PRODUCT_POLICIES] == ["suite", "pos", "sentira", "postpilot"]
    assert [product.name for product in configured_products({})] == ["Gaatha Suite", "Gaatha POS", "Sentira", "PostPilot"]
    assert all(policy.reason and policy.required_deployment_validation for policy in PRODUCT_POLICIES)
    _, body = response()
    assert body.count("Public entry is not available.") == 4
    assert "Phoenix" not in body and "Gaatha AI" not in body and "Gaatha Terra" not in body


def test_postpilot_cannot_be_publicly_linked_even_with_an_approved_url():
    postpilot = next(product for product in configured_products({"GAATHA_POSTPILOT_PUBLIC_URL": "https://app.gaatha.tech/postpilot"}) if product.policy.key == "postpilot")
    assert postpilot.policy.state is PublicEntryState.NOT_READY
    assert postpilot.policy.url_environment_variable is None
    assert postpilot.entry_url is None
    _, body = response(environ={"GAATHA_POSTPILOT_PUBLIC_URL": "https://app.gaatha.tech/postpilot"})
    assert "https://app.gaatha.tech/postpilot" not in body
    assert "Open product" not in body


def test_unapproved_urls_are_rejected_and_never_leak_to_the_page():
    for value in ("http://app.gaatha.tech/suite", "https://localhost/suite", "https://192.168.1.10/suite", "https://internal/suite", "https://user:pass@app.gaatha.tech/suite"):
        assert approved_public_url(value) is None
    _, body = response(environ={"GAATHA_SUITE_PUBLIC_URL": "http://internal:3000", "GAATHA_POS_PUBLIC_URL": "https://other.gaatha.tech/pos"})
    assert "internal:3000" not in body and "other.gaatha.tech" not in body


def test_conditional_products_cannot_bypass_policy_with_a_configured_url():
    products = configured_products({"GAATHA_SUITE_PUBLIC_URL": "https://app.gaatha.tech/suite", "GAATHA_POS_PUBLIC_URL": "https://app.gaatha.tech/pos", "GAATHA_SENTIRA_PUBLIC_URL": "https://app.gaatha.tech/sentira"})
    assert all(product.entry_url is None for product in products)
    _, body = response(environ={"GAATHA_SUITE_PUBLIC_URL": "https://app.gaatha.tech/suite"})
    assert "https://app.gaatha.tech/suite" not in body
    assert body.count(PublicEntryState.CONDITIONAL.value) == 3


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
