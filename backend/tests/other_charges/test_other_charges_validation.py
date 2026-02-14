import time
from tests.utils_auth import _register, _login

API_PRODUCTS = "/api/products"
API_CHARGES = "/api/frais-annexes"


def test_other_charges_rejects_both_lot_and_product(client):
    _register(client)
    _login(client)

    uniq = int(time.time())

    # create product
    r_prod = client.post(API_PRODUCTS, json={"nom": f"Produit OC xor {uniq}", "description": "xor"})
    assert r_prod.status_code == 201
    produit_id = r_prod.get_json()["id"]

    try:
        # invalid payload: neither lot_id nor produit_id
        r_bad1 = client.post(API_CHARGES, json={"intitule": "bad", "montant": 1.0})
        assert r_bad1.status_code == 400

        # invalid payload: both lot_id and produit_id
        r_bad2 = client.post(
            API_CHARGES,
            json={"intitule": "bad2", "montant": 1.0, "produit_id": produit_id, "lot_id": 1},
        )
        assert r_bad2.status_code == 400

    finally:
        client.delete(f"{API_PRODUCTS}/{produit_id}")
