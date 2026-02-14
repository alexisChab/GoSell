import time
from tests.utils_auth import _register, _login

API_PRODUCTS = "/api/products"
API_CHARGES = "/api/frais-annexes"


def test_post_patch_get_and_delete_other_charge_on_product(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    produit_id = None
    charge_id = None

    try:
        # 1) create product (minimal)
        r_prod = client.post(
            API_PRODUCTS,
            json={"nom": f"Produit OC {uniq}", "description": "test other charges"},
        )
        assert r_prod.status_code == 201
        produit_id = r_prod.get_json()["id"]

        # 2) create other charge linked to product
        r_post = client.post(
            API_CHARGES,
            json={
                "intitule": f"Frais annexe {uniq}",
                "montant": 9.99,
                "produit_id": produit_id,
            },
        )
        assert r_post.status_code == 201
        created = r_post.get_json()
        assert "id" in created
        charge_id = created["id"]
        assert created["produit_id"] == produit_id
        assert created["lot_id"] is None

        # 3) get by id
        r_get = client.get(f"{API_CHARGES}/{charge_id}")
        assert r_get.status_code == 200
        got = r_get.get_json()
        assert got["id"] == charge_id
        assert got["produit_id"] == produit_id

        # 4) patch
        r_patch = client.patch(
            f"{API_CHARGES}/{charge_id}",
            json={"montant": 12.34, "intitule": f"Frais annexe patched {uniq}"},
        )
        assert r_patch.status_code == 200
        patched = r_patch.get_json()
        assert patched["id"] == charge_id
        assert patched["montant"] == 12.34
        assert patched["intitule"] == f"Frais annexe patched {uniq}"

        # 5) delete
        r_del = client.delete(f"{API_CHARGES}/{charge_id}")
        assert r_del.status_code == 200
        assert r_del.get_json()["ok"] is True

        # 6) get after delete -> 404
        r_get2 = client.get(f"{API_CHARGES}/{charge_id}")
        assert r_get2.status_code == 404

    finally:
        # cleanup idempotent
        if charge_id is not None:
            client.delete(f"{API_CHARGES}/{charge_id}")

        if produit_id is not None:
            client.delete(f"{API_PRODUCTS}/{produit_id}")
