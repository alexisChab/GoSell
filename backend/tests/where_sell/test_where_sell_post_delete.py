import time
from tests.utils_auth import _register, _login

API_PRODUCTS = "/api/products"
API_PLATFORMS = "/api/platforms"
API_WHERE_SELL = "/api/ou-ventes"


def test_post_patch_get_and_delete_where_sell(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    produit_id = None
    plateforme_id = None

    # 1) Create product
    r_prod = client.post(API_PRODUCTS, json={"nom": f"Produit ou_vente {uniq}", "description": "pytest"})
    assert r_prod.status_code == 201
    produit_id = r_prod.get_json()["id"]

    # 2) Create platform
    r_plat = client.post(API_PLATFORMS, json={"nom": f"Plateforme ou_vente {uniq}"})
    assert r_plat.status_code in (201, 409)
    if r_plat.status_code == 409:
        # Si tu as une contrainte d'unicité sur "nom" et conflit ultra rare,
        # tu peux relancer avec un autre uniq. Ici on fail explicitement.
        raise AssertionError("Platform already exists (409) - retry with another uniq")
    plateforme_id = r_plat.get_json()["id"]

    try:
        # 3) POST where_sell
        r_post = client.post(
            API_WHERE_SELL,
            json={"produit_id": produit_id, "plateforme_id": plateforme_id, "lien": "https://example.com/item"},
        )
        assert r_post.status_code in (201, 409)

        # 4) GET where_sell (PK composite)
        r_get = client.get(f"{API_WHERE_SELL}/{produit_id}/{plateforme_id}")
        assert r_get.status_code == 200
        body = r_get.get_json()
        assert body["produit_id"] == produit_id
        assert body["plateforme_id"] == plateforme_id

        # 5) PATCH lien
        r_patch = client.patch(
            f"{API_WHERE_SELL}/{produit_id}/{plateforme_id}",
            json={"lien": "https://example.com/item-updated"},
        )
        assert r_patch.status_code == 200
        patched = r_patch.get_json()
        assert patched["lien"] == "https://example.com/item-updated"

        # 6) DELETE where_sell
        r_del = client.delete(f"{API_WHERE_SELL}/{produit_id}/{plateforme_id}")
        assert r_del.status_code in (200, 204)

        # 7) GET not found after delete
        r_get2 = client.get(f"{API_WHERE_SELL}/{produit_id}/{plateforme_id}")
        assert r_get2.status_code == 404

    finally:
        # Cleanup hard (idempotent)
        if produit_id is not None and plateforme_id is not None:
            client.delete(f"{API_WHERE_SELL}/{produit_id}/{plateforme_id}")
        if produit_id is not None:
            client.delete(f"{API_PRODUCTS}/{produit_id}")
        if plateforme_id is not None:
            client.delete(f"{API_PLATFORMS}/{plateforme_id}")
