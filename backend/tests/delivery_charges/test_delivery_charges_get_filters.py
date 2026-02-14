import time
from tests.utils_auth import _register, _login

API_PRODUCTS = "/api/products"
API_DELIVERY = "/api/frais-livraison"


def test_delivery_charges_get_list_with_filters(client):
    _register(client)
    _login(client)

    uniq = int(time.time())

    produit_id = None
    charge_id = None

    try:
        # create product
        r_prod = client.post(
            API_PRODUCTS,
            json={"nom": f"Produit filt delivery {uniq}", "description": "filter"},
        )
        assert r_prod.status_code == 201
        produit_id = r_prod.get_json()["id"]

        # create delivery charge
        r_post = client.post(
            API_DELIVERY,
            json={"montant": 5.25, "produit_id": produit_id},
        )
        assert r_post.status_code == 201
        charge_id = r_post.get_json()["id"]

        # filter by produit_id
        r = client.get(
            f"{API_DELIVERY}?produit_id={produit_id}&page=1&page_size=50&order_by=id&order_dir=desc"
        )
        assert r.status_code == 200

        ids = {x["id"] for x in r.get_json()}
        assert charge_id in ids

    finally:
        if charge_id is not None:
            client.delete(f"{API_DELIVERY}/{charge_id}")
        if produit_id is not None:
            client.delete(f"{API_PRODUCTS}/{produit_id}")
