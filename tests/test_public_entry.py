from public_entry import approved_public_url, configured_products, public_entry_app


def response(path="/", environ=None):
    captured = {}
    result = public_entry_app({"PATH_INFO": path, **(environ or {})}, lambda status, headers: captured.update(status=status, headers=headers))
    return captured, b"".join(result).decode()


def test_public_page_lists_exactly_four_products_and_defaults_to_not_connected():
    _, body = response()
    assert [product.name for product in configured_products({})] == ["Gaatha Suite", "Gaatha POS", "Sentira", "PostPilot"]
    assert body.count("Not yet connected") == 4
    assert "Phoenix" not in body and "Gaatha AI" not in body and "Gaatha Terra" not in body


def test_only_approved_https_public_urls_render_product_links():
    assert approved_public_url("http://app.gaatha.tech/suite") is None
    assert approved_public_url("https://localhost/suite") is None
    assert approved_public_url("https://192.168.1.10/suite") is None
    assert approved_public_url("https://internal/suite") is None
    assert approved_public_url("https://user:pass@app.gaatha.tech/suite") is None
    captured, body = response(environ={"GAATHA_SUITE_PUBLIC_URL": "https://app.gaatha.tech/suite", "GAATHA_POS_PUBLIC_URL": "http://internal:3000"})
    assert captured["status"] == "200 OK"
    assert "https://app.gaatha.tech/suite" in body
    assert "http://internal:3000" not in body
    assert body.count("Entry configured") == 1


def test_public_routes_are_safe_and_health_does_not_disclose_dependencies():
    captured, health = response("/healthz")
    assert captured["status"] == "200 OK"
    assert health == '{"status":"available"}'
    captured, body = response("/missing")
    assert captured["status"] == "404 Not Found"
    assert body == "Not found"
