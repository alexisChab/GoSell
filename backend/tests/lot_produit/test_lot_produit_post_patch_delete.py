import time
from tests.utils_auth import _register, _login


API_LOTS = "/api/lots"
API_PRODUCTS = "/api/products"
API_LOT_PRODUITS = "/api/lot-produits"


def test_post_patch_get_and_delete_lot_produit(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    lot_id = None
    produit_id = None
    lot_produit_id = None

    try:
        r_lot = client.post(
            API_LOTS,
            json={
                "titre": f"Lot LP {uniq}",
                "prix_total_achat": 100.0,
            },
        )
        assert r_lot.status_code == 201
        lot_id = r_lot.get_json()["id"]

        r_prod = client.post(
            API_PRODUCTS,
            json={
                "nom": f"Produit LP {uniq}",
                "description": "test pivot",
            },
        )
        assert r_prod.status_code == 201
        produit_id = r_prod.get_json()["id"]

        r_lp = client.post(
            API_LOT_PRODUITS,
            json={
                "lot_id": lot_id,
                "produit_id": produit_id,
                "quantite": 2,
                "allocation_methode": "manual",
            },
        )
        assert r_lp.status_code == 201
        created = r_lp.get_json()
        lot_produit_id = created["id"]

        assert created["lot_id"] == lot_id
        assert created["produit_id"] == produit_id
        assert created["quantite"] == 2

        r_patch = client.patch(
            f"{API_LOT_PRODUITS}/{lot_produit_id}",
            json={
                "quantite": 5,
                "allocation_prix_achat": 60.0,
            },
        )
        assert r_patch.status_code == 200
        patched = r_patch.get_json()
        assert patched["quantite"] == 5
        assert patched["allocation_prix_achat"] == 60.0

        r_get = client.get(f"{API_LOT_PRODUITS}/{lot_produit_id}")
        assert r_get.status_code == 200
        got = r_get.get_json()
        assert got["id"] == lot_produit_id

        r_del = client.delete(f"{API_LOT_PRODUITS}/{lot_produit_id}")
        assert r_del.status_code == 200

        r_get2 = client.get(f"{API_LOT_PRODUITS}/{lot_produit_id}")
        assert r_get2.status_code == 404

    finally:
        # Cleanup idempotent
        if lot_produit_id is not None:
            client.delete(f"{API_LOT_PRODUITS}/{lot_produit_id}")

        if lot_id is not None:
            client.delete(f"{API_LOTS}/{lot_id}")

        if produit_id is not None:
            client.delete(f"{API_PRODUCTS}/{produit_id}")
