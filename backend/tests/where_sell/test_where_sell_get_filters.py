import time
from tests.utils_auth import _register, _login

API_PRODUCTS = "/api/products"
API_PLATFORMS = "/api/platforms"
API_WHERE_SELL = "/api/ou-ventes"


def test_where_sells_get_list_with_filters(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    produit_id = None
    plateforme_id = None

    # create product
    r_prod = client.post(API_PRODUCTS, json={"nom": f"Produit filt ou_vente {uniq}", "description": "pytest"})
    assert r_prod.status_code == 201
    produit_id = r_prod.get_json()["id"]

    # create platform
    r_plat = client.post(API_PLATFORMS, json={"nom": f"Plateforme filt ou_vente {uniq}"})
    assert r_plat.status_code == 201
    plateforme_id = r_plat.get_json()["id"]

    try:
        # create where_sell
        r_post = client.post(
            API_WHERE_SELL,
            json={"produit_id": produit_id, "plateforme_id": plateforme_id, "lien": None},
        )
        assert r_post.status_code in (201, 409)

        # filter by produit_id
        r = client.get(f"{API_WHERE_SELL}?produit_id={produit_id}&page=1&page_size=20")
        assert r.status_code == 200
        body = r.get_json()
        assert isinstance(body, list)
        assert any(
            x["produit_id"] == produit_id and x["plateforme_id"] == plateforme_id
            for x in body
        )

        # filter by plateforme_id
        r2 = client.get(f"{API_WHERE_SELL}?plateforme_id={plateforme_id}&page=1&page_size=20")
        assert r2.status_code == 200
        body2 = r2.get_json()
        assert any(
            x["produit_id"] == produit_id and x["plateforme_id"] == plateforme_id
            for x in body2
        )

    finally:
        # cleanup
        if produit_id is not None and plateforme_id is not None:
            client.delete(f"{API_WHERE_SELL}/{produit_id}/{plateforme_id}")
        if produit_id is not None:
            client.delete(f"{API_PRODUCTS}/{produit_id}")
        if plateforme_id is not None:
            client.delete(f"{API_PLATFORMS}/{plateforme_id}")
