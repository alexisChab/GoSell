import time


def _register(client, email="alexis.test59@local.dev", password="Test1234!"):
    payload = {
        "name": "Alexis",
        "email": email,
        "password": password,
        "pro": False,
    }
    return client.post("/api/auth/register", json=payload)


def _login(client, email="alexis.test59@local.dev", password="Test1234!"):
    payload = {"email": email, "password": password}
    return client.post("/api/auth/login", json=payload)


def test_patch_product(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())
    post_payload = {
        "nom": f"Produit pytest patch {uniq}",
        "description": "avant patch",
        "prix_achat": 10,
        "prix_vente": 25,
        "en_vente": True,
    }

    r_post = client.post("/api/products", json=post_payload)
    assert r_post.status_code == 201
    product = r_post.get_json()
    product_id = product["id"]

    try:
        patch_payload = {
            "description": "après patch",
            "prix_vente": 30,
            "en_vente": False,
        }

        r_patch = client.patch(f"/api/products/{product_id}", json=patch_payload)
        assert r_patch.status_code == 200
        patched = r_patch.get_json()

        assert patched["id"] == product_id
        assert patched["description"] == "après patch"
        assert patched["prix_vente"] == 30
        assert patched["en_vente"] is False

    finally:
        r_del = client.delete(f"/api/products/{product_id}")
        assert r_del.status_code in (200, 204)
