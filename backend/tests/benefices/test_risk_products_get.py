from utils_auth import _register, _login


def test_risk_products_requires_auth(client):
    r = client.get("/api/risk-products")
    assert r.status_code in (401, 422)


def test_risk_products_ok(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/risk-products?limit=20")
    assert r.status_code == 200
    data = r.get_json()

    assert "items" in data and isinstance(data["items"], list)
    assert "count" in data and isinstance(data["count"], int)
    assert data["count"] == len(data["items"])

    # structure item (si liste non vide)
    if data["items"]:
        it = data["items"][0]
        for k in ("product_id", "from_lot", "median_expected", "cost_total", "profit_amount", "multiple", "risk_level", "reason"):
            assert k in it


def test_risk_products_validation(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/risk-products?limit=0")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"