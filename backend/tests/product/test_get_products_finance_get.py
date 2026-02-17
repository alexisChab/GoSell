from marshmallow import ValidationError

from utils_auth import _register, _login


def test_product_finance_requires_auth(client):
    # Sans JWT => 401 (ou 422 selon config flask-jwt-extended)
    r = client.get("/api/products/1/finance")
    assert r.status_code in (401, 422)


def test_product_finance_not_found_when_logged_in(client):
    # Login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    # ID improbable
    r = client.get("/api/products/99999999/finance")
    assert r.status_code == 404
    body = r.get_json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


def test_product_finance_get_ok_from_first_product(client):
    # Login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    # Récupérer une liste de produits
    r_list = client.get("/api/products")
    assert r_list.status_code == 200
    products = r_list.get_json()
    assert isinstance(products, list)

    # S'il n'y a aucun produit (rare chez toi, mais on sécurise)
    if len(products) == 0:
        # on crée un produit pour pouvoir tester la route finance
        product_payload = {
            "nom": "Produit pytest finance",
            "description": "Temp",
            "a_ete_achete": False,  # gratuit -> doit calculer avec cout_achat=0
            "prix_min_espere": 10,
            "prix_max_espere": 20,
            "en_vente": True,
        }
        r_post = client.post("/api/products", json=product_payload)
        assert r_post.status_code == 201
        product_id = r_post.get_json()["id"]
    else:
        product_id = products[0]["id"]

    # Appel finance
    r_fin = client.get(f"/api/products/{product_id}/finance")
    assert r_fin.status_code == 200
    data = r_fin.get_json()

    # --- Assertions structure ---
    assert data["produit_id"] == product_id
    assert "from_lot" in data
    assert "a_ete_achete" in data

    assert "prix" in data and isinstance(data["prix"], dict)
    assert "min_espere" in data["prix"]
    assert "max_espere" in data["prix"]
    assert "median_espere" in data["prix"]

    assert "fees" in data and isinstance(data["fees"], dict)
    assert "delivery_fees" in data["fees"]
    assert "other_fees" in data["fees"]
    assert "total_fees" in data["fees"]

    assert "costs" in data and isinstance(data["costs"], dict)
    assert "cout_achat" in data["costs"]
    assert "cout_total" in data["costs"]

    assert "profit" in data and isinstance(data["profit"], dict)
    assert "benefice_espere" in data["profit"]
    assert "is_benefice_espere" in data["profit"]
    assert "reason" in data["profit"]

    # --- Règles métier minimales ---
    if data["from_lot"] is True:
        # Pas de calcul au niveau produit
        assert data["profit"]["reason"] == "CALCUL_AU_NIVEAU_DU_LOT"
        assert data["profit"]["benefice_espere"] is None
        assert data["profit"]["is_benefice_espere"] is None
    else:
        # Si prix median dispo, alors on attend un résultat ou une raison claire
        median = data["prix"]["median_espere"]

        if median is None:
            assert data["profit"]["reason"] == "PRIX_ESPERES_INSUFFISANTS"
            assert data["profit"]["benefice_espere"] is None
            assert data["profit"]["is_benefice_espere"] is None
        else:
            # cas gratuit OU acheté
            if data["a_ete_achete"] is False:
                # cout_achat doit être 0 (ou None si tu as décidé autrement)
                assert data["costs"]["cout_achat"] in (0, 0.0)

                # On doit calculer un bénéfice espéré (= median - cout_total)
                # cout_total = frais (>=0)
                assert data["costs"]["cout_total"] is not None
                assert data["profit"]["benefice_espere"] is not None
                assert isinstance(data["profit"]["is_benefice_espere"], bool)

            else:
                # acheté: si prix_achat manquant -> reason PRIX_ACHAT_MANQUANT
                if data["costs"]["cout_achat"] is None:
                    assert data["profit"]["reason"] == "PRIX_ACHAT_MANQUANT"
                    assert data["profit"]["benefice_espere"] is None
                    assert data["profit"]["is_benefice_espere"] is None
                else:
                    # sinon on doit avoir le calcul
                    assert data["costs"]["cout_total"] is not None
                    assert data["profit"]["benefice_espere"] is not None
                    assert isinstance(data["profit"]["is_benefice_espere"], bool)
