import pytest

from utils_auth import _register, _login


def _assert_kpi_shape(kpi: dict):
    assert isinstance(kpi, dict)
    for k in ("price", "cost_total", "profit_amount", "multiple", "is_profit"):
        assert k in kpi


def _assert_forecast_shape(data: dict):
    assert "product_id" in data
    assert "from_lot" in data
    assert "a_ete_achete" in data
    assert "haircut_percent" in data
    assert "cost_total" in data
    assert "scenarios" in data and isinstance(data["scenarios"], dict)
    assert "reason" in data

    for key in ("min", "median", "max"):
        assert key in data["scenarios"]
        _assert_kpi_shape(data["scenarios"][key])

    # offer est optionnel (None ou dict)
    assert "offer" in data["scenarios"]
    if data["scenarios"]["offer"] is not None:
        _assert_kpi_shape(data["scenarios"]["offer"])


def _assert_whatif_shape(data: dict):
    assert "product_id" in data
    assert "from_lot" in data
    assert "a_ete_achete" in data
    assert "offer" in data and isinstance(data["offer"], dict)
    assert "reason" in data
    _assert_kpi_shape(data["offer"])


def _get_any_product_id(client) -> int:
    r_list = client.get("/api/products")
    assert r_list.status_code == 200
    products = r_list.get_json()
    assert isinstance(products, list)

    if len(products) == 0:
        # fallback : créer un produit minimal
        payload = {
            "nom": "Produit pytest whatif",
            "a_ete_achete": False,         # gratuit => coût achat 0
            "prix_min_espere": 10,
            "prix_max_espere": 20,
            "en_vente": True,
        }
        r_post = client.post("/api/products", json=payload)
        assert r_post.status_code == 201
        return r_post.get_json()["id"]

    return products[0]["id"]


def test_product_whatif_requires_auth(client):
    r = client.get("/api/products/1/whatif?offer_price=30")
    assert r.status_code in (401, 422)


def test_product_forecast_requires_auth(client):
    r = client.get("/api/products/1/forecast")
    assert r.status_code in (401, 422)


def test_product_whatif_validation_error(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # offer_price obligatoire
    r = client.get("/api/products/1/whatif")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"

    # offer_price négatif
    r2 = client.get("/api/products/1/whatif?offer_price=-1")
    assert r2.status_code == 400
    body2 = r2.get_json()
    assert body2["error"]["code"] == "VALIDATION_ERROR"


def test_product_forecast_validation_error(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # haircut_percent > 100
    r = client.get("/api/products/1/forecast?haircut_percent=200")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"

    # offer_price négatif
    r2 = client.get("/api/products/1/forecast?offer_price=-1")
    assert r2.status_code == 400
    body2 = r2.get_json()
    assert body2["error"]["code"] == "VALIDATION_ERROR"


def test_product_whatif_not_found(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/products/99999999/whatif?offer_price=30")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_product_forecast_not_found(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/products/99999999/forecast")
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_product_whatif_ok(client):
    # login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    product_id = _get_any_product_id(client)

    r = client.get(f"/api/products/{product_id}/whatif?offer_price=30")
    assert r.status_code == 200
    data = r.get_json()
    _assert_whatif_shape(data)

    assert data["product_id"] == product_id

    # Si from_lot => pas de calcul (cost_total None, profit_amount None, multiple None)
    if data["from_lot"] is True:
        assert data["reason"] == "CALCUL_AU_NIVEAU_DU_LOT"
        assert data["offer"]["cost_total"] is None
        assert data["offer"]["profit_amount"] is None
        assert data["offer"]["multiple"] is None
        assert data["offer"]["is_profit"] is None
        return

    # Sinon, si coût total calculable
    if data["offer"]["cost_total"] is not None:
        cost_total = float(data["offer"]["cost_total"])
        price = float(data["offer"]["price"])
        profit = float(data["offer"]["profit_amount"])

        assert abs((price - cost_total) - profit) < 1e-6

        # multiple si cost_total>0
        if cost_total > 0:
            assert data["offer"]["multiple"] is not None
            assert abs((price / cost_total) - float(data["offer"]["multiple"])) < 1e-6
        else:
            # coût 0 => multiple None + reason ZERO_COST possible
            assert data["offer"]["multiple"] is None
            assert data["reason"] in (None, "ZERO_COST")


def test_product_forecast_ok_min_median_max(client):
    # login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    product_id = _get_any_product_id(client)

    r = client.get(f"/api/products/{product_id}/forecast")
    assert r.status_code == 200
    data = r.get_json()
    _assert_forecast_shape(data)

    assert data["product_id"] == product_id

    if data["from_lot"] is True:
        assert data["reason"] == "CALCUL_AU_NIVEAU_DU_LOT"
        assert data["cost_total"] is None
        # scénarios doivent être vides (price None etc.)
        assert data["scenarios"]["min"]["price"] is None
        assert data["scenarios"]["median"]["price"] is None
        assert data["scenarios"]["max"]["price"] is None
        return

    # Si coût total existe, les KPI doivent être cohérents quand le price existe
    cost_total = data["cost_total"]
    if cost_total is not None:
        cost_total = float(cost_total)
        for key in ("min", "median", "max"):
            kpi = data["scenarios"][key]
            if kpi["price"] is None:
                continue
            price = float(kpi["price"])
            profit = float(kpi["profit_amount"])
            assert abs((price - cost_total) - profit) < 1e-6

            if cost_total > 0:
                assert kpi["multiple"] is not None
                assert abs((price / cost_total) - float(kpi["multiple"])) < 1e-6
            else:
                assert kpi["multiple"] is None


def test_product_forecast_offer_and_haircut(client):
    # login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    product_id = _get_any_product_id(client)

    # offer + haircut
    r = client.get(f"/api/products/{product_id}/forecast?offer_price=30&haircut_percent=20")
    assert r.status_code == 200
    data = r.get_json()
    _assert_forecast_shape(data)

    assert data["haircut_percent"] in (20, 20.0)

    # offer doit exister (dict) si offer_price fourni, sauf from_lot/cost_total None
    if data["from_lot"] is True or data["cost_total"] is None:
        return

    assert data["scenarios"]["offer"] is not None
    offer_kpi = data["scenarios"]["offer"]
    _assert_kpi_shape(offer_kpi)

    # haircut 20% sur offer_price=30 => price = 24
    assert abs(float(offer_kpi["price"]) - 24.0) < 1e-6
