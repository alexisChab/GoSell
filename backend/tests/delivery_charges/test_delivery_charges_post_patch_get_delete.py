import time
from tests.utils_auth import _register, _login

API_PRODUCTS = "/api/products"
API_DELIVERY = "/api/frais-livraison"


def test_post_patch_get_and_delete_delivery_charge(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    produit_id = None
    charge_id = None

    try:
        # 1️⃣ create product
        r_prod = client.post(
            API_PRODUCTS,
            json={"nom": f"Produit delivery {uniq}", "description": "delivery test"},
        )
        assert r_prod.status_code == 201
        produit_id = r_prod.get_json()["id"]

        # 2️⃣ create delivery charge
        r_post = client.post(
            API_DELIVERY,
            json={
                "montant": 15.50,
                "produit_id": produit_id,
            },
        )
        assert r_post.status_code == 201
        charge = r_post.get_json()
        charge_id = charge["id"]

        assert charge["produit_id"] == produit_id
        assert charge["montant"] == 15.50

        # 3️⃣ get by id
        r_get = client.get(f"{API_DELIVERY}/{charge_id}")
        assert r_get.status_code == 200
        assert r_get.get_json()["id"] == charge_id

        # 4️⃣ patch
        r_patch = client.patch(
            f"{API_DELIVERY}/{charge_id}",
            json={"montant": 19.99},
        )
        assert r_patch.status_code == 200
        assert r_patch.get_json()["montant"] == 19.99

        # 5️⃣ delete
        r_del = client.delete(f"{API_DELIVERY}/{charge_id}")
        assert r_del.status_code == 200
        assert r_del.get_json()["ok"] is True

        # 6️⃣ ensure deleted
        r_get2 = client.get(f"{API_DELIVERY}/{charge_id}")
        assert r_get2.status_code == 404

    finally:
        # cleanup safe
        if charge_id is not None:
            client.delete(f"{API_DELIVERY}/{charge_id}")
        if produit_id is not None:
            client.delete(f"{API_PRODUCTS}/{produit_id}")
