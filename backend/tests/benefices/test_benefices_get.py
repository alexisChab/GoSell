from utils_auth import _register, _login
import pytest

def _assert_benefice_payload_shape(data: dict):
    assert "scope" in data and isinstance(data["scope"], dict)
    assert "counts" in data and isinstance(data["counts"], dict)
    assert "totals" in data and isinstance(data["totals"], dict)

    # scope
    for k in ("include_products", "include_stocks", "include_fees"):
        assert k in data["scope"]
        assert isinstance(data["scope"][k], bool)

    # counts
    for k in (
        "nb_produits",
        "nb_stocks",
        "nb_produits_ignored_missing_expected",
        "nb_produits_ignored_missing_cost",
    ):
        assert k in data["counts"]
        assert isinstance(data["counts"][k], int)
        assert data["counts"][k] >= 0

    # totals
    for k in (
        "cost_products",
        "cost_stocks",
        "fees",
        "cost_total",
        "revenue_expected_median",
        "profit_expected_median",
        "is_profit_expected_median",
    ):
        assert k in data["totals"]

    assert isinstance(data["totals"]["is_profit_expected_median"], bool)


def _assert_totals_consistency(data: dict):
    totals = data["totals"]

    # cost_total = cost_products + cost_stocks + fees
    cp = float(totals["cost_products"])
    cs = float(totals["cost_stocks"])
    fees = float(totals["fees"])
    cost_total = float(totals["cost_total"])
    assert abs((cp + cs + fees) - cost_total) < 1e-6

    # profit = revenue_expected_median - cost_total
    rev = float(totals["revenue_expected_median"])
    prof = float(totals["profit_expected_median"])
    assert abs((rev - cost_total) - prof) < 1e-6

    # bool cohérent
    assert totals["is_profit_expected_median"] == (prof > 0)


def test_benefices_requires_auth(client):
    r = client.get("/api/benefices")
    assert r.status_code in (401, 422)


def test_benefices_validation_error_on_bad_query(client):
    # login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    # champ bool invalid (selon marshmallow, ça peut lever ValidationError)
    r = client.get("/api/benefices?include_products=notabool")
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_benefices_default_ok(client):
    # login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/benefices")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    _assert_totals_consistency(data)


def test_benefices_only_products(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices?include_stocks=false")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    assert data["scope"]["include_stocks"] is False
    # si stocks exclus => cost_stocks = 0 et nb_stocks = 0 (logique attendue)
    assert data["counts"]["nb_stocks"] == 0
    assert float(data["totals"]["cost_stocks"]) == 0.0

    _assert_totals_consistency(data)


def test_benefices_only_stocks(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices?include_products=false")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    assert data["scope"]["include_products"] is False
    # produits exclus => revenue_expected_median = 0, cost_products = 0 et nb_produits = 0
    assert data["counts"]["nb_produits"] == 0
    assert float(data["totals"]["cost_products"]) == 0.0
    assert float(data["totals"]["revenue_expected_median"]) == 0.0

    _assert_totals_consistency(data)


def test_benefices_exclude_fees(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices?include_fees=false")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    assert data["scope"]["include_fees"] is False
    assert float(data["totals"]["fees"]) == 0.0

    _assert_totals_consistency(data)


def test_benefices_products_filters_flags(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # filtre sur produits en vente + achetés
    r = client.get("/api/benefices?include_stocks=false&products_en_vente=true&products_a_ete_achete=true")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    assert data["scope"]["include_stocks"] is False
    _assert_totals_consistency(data)


def test_benefices_products_filter_by_ids(client):
    # login
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # on récupère des produits existants pour construire product_ids
    r_list = client.get("/api/products")
    assert r_list.status_code == 200
    products = r_list.get_json()
    assert isinstance(products, list)

    if len(products) == 0:
        # fallback: créer 2 produits rapides
        p1 = {"nom": "P1", "a_ete_achete": False, "prix_min_espere": 10, "prix_max_espere": 20}
        p2 = {"nom": "P2", "a_ete_achete": True, "prix_achat": 5, "prix_min_espere": 10, "prix_max_espere": 20}
        r1 = client.post("/api/products", json=p1); assert r1.status_code == 201
        r2 = client.post("/api/products", json=p2); assert r2.status_code == 201
        ids = [r1.get_json()["id"], r2.get_json()["id"]]
    else:
        ids = [products[0]["id"]]
        if len(products) > 1:
            ids.append(products[1]["id"])

    ids_csv = ",".join(str(i) for i in ids)

    r = client.get(f"/api/benefices?include_stocks=false&product_ids={ids_csv}")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    assert data["scope"]["include_stocks"] is False
    _assert_totals_consistency(data)


def test_benefices_exclude_lot_products_flag(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # Juste vérifier que l’endpoint répond (le dataset peut ou non avoir des produits en lot)
    r = client.get("/api/benefices?include_stocks=false&exclude_lot_products=true")
    assert r.status_code == 200
    data = r.get_json()

    _assert_benefice_payload_shape(data)
    _assert_totals_consistency(data)
def test_benefices_filter_by_type_produit_or_genre(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # On essaye de récupérer un type_produit existant
    r_types = client.get("/api/type_produit")
    if r_types.status_code == 404:
        pytest.skip("Endpoint /api/type_produit non présent dans ce projet")
    assert r_types.status_code == 200
    types = r_types.get_json()
    assert isinstance(types, list)

    if len(types) == 0:
        # Si pas de type_produit dans la DB de test, on teste quand même que la route répond
        r = client.get("/api/benefices?include_stocks=false&type_produit_id=1")
        assert r.status_code == 200
        data = r.get_json()
        _assert_benefice_payload_shape(data)
        _assert_totals_consistency(data)
        return

    type_id = types[0]["id"]

    # Filtre par type_produit_id
    r = client.get(f"/api/benefices?include_stocks=false&type_produit_id={type_id}")
    assert r.status_code == 200
    data = r.get_json()
    _assert_benefice_payload_shape(data)
    _assert_totals_consistency(data)

    # Optionnel: filtre par genre_id si endpoint existe
    r_genres = client.get("/api/genres")
    if r_genres.status_code == 404:
        # pas grave : on s’arrête ici
        return
    assert r_genres.status_code == 200
    genres = r_genres.get_json()
    assert isinstance(genres, list)

    if len(genres) == 0:
        return

    genre_id = genres[0]["id"]
    r2 = client.get(f"/api/benefices?include_stocks=false&genre_id={genre_id}")
    assert r2.status_code == 200
    data2 = r2.get_json()
    _assert_benefice_payload_shape(data2)
    _assert_totals_consistency(data2)


def test_benefices_stocks_filter_by_prix_achat_range(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    # Vérifier si endpoint GET /stocks existe (sinon skip)
    r_stocks = client.get("/api/stocks")
    if r_stocks.status_code == 404:
        pytest.skip("Endpoint /api/stocks non présent dans ce projet")
    assert r_stocks.status_code == 200
    stocks = r_stocks.get_json()
    assert isinstance(stocks, list)

    # Si tu as une route POST /stocks, on peut créer un stock pour être sûr d'avoir de la donnée
    if len(stocks) == 0:
        r_post = client.post("/api/stocks", json={
            "nom": "Stock pytest range",
            "a_ete_achete": True,
            "prix_achat": 50.0
        })
        if r_post.status_code == 404:
            # pas de POST, on continue en mode soft
            pass
        else:
            assert r_post.status_code in (200, 201)

    # Filtre range (doit répondre 200)
    r = client.get("/api/benefices?include_products=false&stocks_prix_achat_min=10&stocks_prix_achat_max=100")
    assert r.status_code == 200
    data = r.get_json()
    _assert_benefice_payload_shape(data)
    _assert_totals_consistency(data)

    # Cas range inversée (selon ton schema, ça peut passer et donner 0 résultats)
    r2 = client.get("/api/benefices?include_products=false&stocks_prix_achat_min=9999&stocks_prix_achat_max=1")
    assert r2.status_code == 200
    data2 = r2.get_json()
    _assert_benefice_payload_shape(data2)
    _assert_totals_consistency(data2)