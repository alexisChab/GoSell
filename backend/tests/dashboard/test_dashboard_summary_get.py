from utils_auth import _register, _login


def test_dashboard_summary_requires_auth(client):
    r = client.get("/api/dashboard/summary")
    assert r.status_code in (401, 422)


def test_dashboard_summary_ok(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    data = r.get_json()

    # shape
    assert "counts" in data and isinstance(data["counts"], dict)
    assert "benefices" in data and isinstance(data["benefices"], dict)
    assert "risk_products" in data and isinstance(data["risk_products"], dict)
    assert "best_types" in data and isinstance(data["best_types"], dict)

    # counts
    for k in ("nb_produits_total", "nb_produits_en_vente", "nb_produits_vendus", "nb_lots", "nb_stocks"):
        assert k in data["counts"]
        assert isinstance(data["counts"][k], int)
        assert data["counts"][k] >= 0

    # benefices (minimum check)
    assert "totals" in data["benefices"]
    assert "profit_expected_median" in data["benefices"]["totals"]

    # risk products
    assert "items" in data["risk_products"]
    assert "count" in data["risk_products"]
    assert data["risk_products"]["count"] == len(data["risk_products"]["items"])
    assert isinstance(data["risk_products"]["items"], list)

    # best types
    assert "items" in data["best_types"]
    assert "count" in data["best_types"]
    assert data["best_types"]["count"] == len(data["best_types"]["items"])
    assert isinstance(data["best_types"]["items"], list)