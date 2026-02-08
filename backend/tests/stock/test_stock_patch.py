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


def test_patch_stock_item(client):
    # register (ok si déjà existant)
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    # login (cookies JWT)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- POST /api/stock
    post_payload = {
        "nom": f"Stock pytest patch {uniq}",
        "description": "avant patch",
        "localisation": "Maison",
        "a_ete_achete": False,
        "prix_achat": 12.5,
    }

    r_post = client.post("/api/stock", json=post_payload)
    assert r_post.status_code == 201
    created = r_post.get_json()
    assert "id" in created

    stock_id = created["id"]

    try:
        # ---- PATCH /api/stock/<id>
        patch_payload = {
            "description": "après patch",
            "a_ete_achete": True,
            "prix_achat": 15.0,
        }

        r_patch = client.patch(f"/api/stock/{stock_id}", json=patch_payload)
        assert r_patch.status_code == 200

        patched = r_patch.get_json()
        assert patched["id"] == stock_id
        assert patched["description"] == "après patch"
        assert patched["a_ete_achete"] is True
        assert float(patched["prix_achat"]) == 15.0

    finally:
        # cleanup (même si un assert casse)
        client.delete(f"/api/stock/{stock_id}")
