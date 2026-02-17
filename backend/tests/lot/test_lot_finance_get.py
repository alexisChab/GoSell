from utils_auth import _register, _login


def test_lot_finance_requires_auth(client):
    r = client.get("/api/lots/1/finance")
    assert r.status_code in (401, 422)


def test_lot_finance_not_found_when_logged_in(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/lots/99999999/finance")
    assert r.status_code == 404
    body = r.get_json()
    # ta route lot renvoie {ok:false, error:"LOT_NOT_FOUND"} :contentReference[oaicite:2]{index=2}
    assert body["ok"] is False
    assert body["error"] == "LOT_NOT_FOUND"


def test_lot_finance_get_ok_from_first_lot(client):
    # --------
    # Register + Login
    # --------
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    # --------
    # GET /lots
    # --------
    r_list = client.get("/api/lots")
    assert r_list.status_code == 200
    lots = r_list.get_json()
    assert isinstance(lots, list)

    # Si aucun lot => on en crée un (comme fallback)
    if len(lots) == 0:
        lot_payload = {
            "titre": "Lot pytest finance",
            "description": "Temp",
            "prix_total_achat": 10.0,
        }
        r_post = client.post("/api/lots", json=lot_payload)
        assert r_post.status_code == 201
        lot_id = r_post.get_json()["id"]
    else:
        lot_id = lots[0]["id"]

    # --------
    # GET /lots/<id>/finance
    # --------
    r_fin = client.get(f"/api/lots/{lot_id}/finance")
    assert r_fin.status_code == 200
    data = r_fin.get_json()

    # --------
    # Assertions structure
    # --------
    assert data["lot_id"] == lot_id

    assert "counts" in data and isinstance(data["counts"], dict)
    assert "nb_produits" in data["counts"]
    assert "nb_vendus" in data["counts"]

    assert "revenue" in data and isinstance(data["revenue"], dict)
    assert "revenue_vendu" in data["revenue"]
    assert "revenue_espere_median" in data["revenue"]

    assert "fees" in data and isinstance(data["fees"], dict)
    assert "lot_other_fees" in data["fees"]
    assert "produits_fees" in data["fees"]
    assert "total_fees" in data["fees"]

    assert "costs" in data and isinstance(data["costs"], dict)
    assert "achat_lot" in data["costs"]
    assert "total_cost" in data["costs"]

    assert "profit" in data and isinstance(data["profit"], dict)
    assert "profit_espere_median" in data["profit"]
    assert "is_profit_espere_median" in data["profit"]
    assert "reason" in data["profit"]

    # --------
    # Assertions métier minimales
    # --------
    # total_cost = achat_lot + total_fees (sauf erreur float minime)
    achat_lot = data["costs"]["achat_lot"]
    total_fees = data["fees"]["total_fees"]
    total_cost = data["costs"]["total_cost"]
    assert abs((achat_lot + total_fees) - total_cost) < 1e-6

    # Si reason PRIX_ESPERES_INSUFFISANTS => revenue_espere_median et profit null
    if data["profit"]["reason"] == "PRIX_ESPERES_INSUFFISANTS":
        assert data["revenue"]["revenue_espere_median"] is None
        assert data["profit"]["profit_espere_median"] is None
        assert data["profit"]["is_profit_espere_median"] is None
    else:
        # sinon, si revenue_espere_median n'est pas None, profit doit être calculé
        rev_med = data["revenue"]["revenue_espere_median"]
        if rev_med is not None:
            assert data["profit"]["profit_espere_median"] is not None
            assert isinstance(data["profit"]["is_profit_espere_median"], bool)
            # profit = revenue_med - total_cost
            assert abs((rev_med - total_cost) - data["profit"]["profit_espere_median"]) < 1e-6
