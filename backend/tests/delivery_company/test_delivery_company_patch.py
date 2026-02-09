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


def test_patch_delivery_company(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- POST
    r_post = client.post("/api/delivery-companies", json={"nom": f"DeliveryCo patch {uniq}"})
    assert r_post.status_code == 201

    created = r_post.get_json()
    dc_id = created["id"]

    try:
        # ---- PATCH
        r_patch = client.patch(f"/api/delivery-companies/{dc_id}", json={"nom": f"DeliveryCo patched {uniq}"})
        assert r_patch.status_code == 200

        patched = r_patch.get_json()
        assert patched["id"] == dc_id
        assert patched["nom"] == f"DeliveryCo patched {uniq}"

    finally:
        client.delete(f"/api/delivery-companies/{dc_id}")
