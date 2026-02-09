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


def test_post_and_delete_delivery_company(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- POST
    post_payload = {"nom": f"DeliveryCo pytest {uniq}"}
    r_post = client.post("/api/delivery-companies", json=post_payload)

    # si conflit (nom unique), ok aussi, mais on ne peut pas delete sans id
    assert r_post.status_code in (201, 409)
    if r_post.status_code == 409:
        return

    created = r_post.get_json()
    assert "id" in created
    assert created["nom"].startswith("DeliveryCo pytest")

    dc_id = created["id"]

    # ---- DELETE (cleanup garanti)
    try:
        r_del = client.delete(f"/api/delivery-companies/{dc_id}")
        assert r_del.status_code in (200, 204)

        if r_del.status_code == 200:
            body = r_del.get_json()
            assert body["ok"] is True
            assert body["deleted_delivery_company_id"] == dc_id
    finally:
        client.delete(f"/api/delivery-companies/{dc_id}")
