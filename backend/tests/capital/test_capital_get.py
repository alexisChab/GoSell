from utils_auth import _register, _login


def test_capital_requires_auth(client):
    r = client.get("/api/capital")
    assert r.status_code in (401, 422)


def test_capital_ok(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/capital")
    assert r.status_code == 200
    data = r.get_json()

    assert "scope" in data and isinstance(data["scope"], dict)
    assert "counts" in data and isinstance(data["counts"], dict)
    assert "totals" in data and isinstance(data["totals"], dict)

    for k in ("capital_products", "capital_lots", "capital_stocks", "capital_total"):
        assert k in data["totals"]
        assert isinstance(data["totals"][k], (int, float))

    # cohérence total
    tot = float(data["totals"]["capital_total"])
    cp = float(data["totals"]["capital_products"])
    cl = float(data["totals"]["capital_lots"])
    cs = float(data["totals"]["capital_stocks"])
    assert abs((cp + cl + cs) - tot) < 1e-6


def test_capital_validation(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # categorie_id doit être >= 1
    r = client.get("/api/capital?categorie_id=0")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"