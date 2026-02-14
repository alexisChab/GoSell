import time
from tests.utils_auth import _register, _login


def test_lot_produit_get_list_with_filters(client):
    _register(client)
    _login(client)

    uniq = int(time.time())

    lot_id = None
    produit_id = None
    lot_produit_id = None

    try:
        # create lot
        r_lot = client.post(
            "/api/lots",
            json={"titre": f"Lot filt LP {uniq}", "prix_total_achat": 50.0},
        )
        assert r_lot.status_code == 201
        lot_id = r_lot.get_json()["id"]

        # create product
        r_prod = client.post(
            "/api/products",
            json={"nom": f"Produit filt LP {uniq}", "description": "test"},
        )
        assert r_prod.status_code == 201
        produit_id = r_prod.get_json()["id"]

        # create pivot
        r_lp = client.post(
            "/api/lot-produits",
            json={"lot_id": lot_id, "produit_id": produit_id, "quantite": 3},
        )
        assert r_lp.status_code == 201
        lot_produit_id = r_lp.get_json()["id"]

        # test filter by lot_id
        r = client.get(f"/api/lot-produits?lot_id={lot_id}")
        assert r.status_code == 200
        body = r.get_json()
        ids = {x["id"] for x in body}
        assert lot_produit_id in ids

    finally:
        if lot_produit_id:
            client.delete(f"/api/lot-produits/{lot_produit_id}")
        if lot_id:
            client.delete(f"/api/lots/{lot_id}")
        if produit_id:
            client.delete(f"/api/products/{produit_id}")
