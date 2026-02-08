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


def test_post_and_delete_stock(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    # login (cookies JWT)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- POST /api/stock
    post_payload = {
        "nom": f"Stock pytest {uniq}",
        "description": "item temporaire pour test",
        "localisation": "Maison",
        "a_ete_achete": True,
        "prix_achat": 12.5,
    }

    r_post = client.post("/api/stock", json=post_payload)
    assert r_post.status_code == 201

    item = r_post.get_json()
    assert "id" in item
    assert item["nom"].startswith("Stock pytest")

    stock_id = item["id"]

    # ---- DELETE /api/stock/<id> (cleanup garanti)
    try:
        r_del = client.delete(f"/api/stock/{stock_id}")
        assert r_del.status_code in (200, 204)

        if r_del.status_code == 200:
            body = r_del.get_json()
            assert body["ok"] is True
            assert body["deleted_stock_id"] == stock_id
    finally:
        client.delete(f"/api/stock/{stock_id}")
