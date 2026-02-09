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


def test_post_and_delete_platform(client):
    # register (ok si déjà existant)
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    # login (cookies JWT)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    post_payload = {
        "nom": f"Plateforme pytest {uniq}",
        "frais_supp_eur": 2.5,
        "pourcentage_vente": 10.0,
        "lien_homepage": "https://example.com",
    }

    r_post = client.post("/api/platforms", json=post_payload)
    assert r_post.status_code in (201, 409)

    if r_post.status_code == 409:
        return

    created = r_post.get_json()
    assert "id" in created
    assert created["nom"].startswith("Plateforme pytest")
    platform_id = created["id"]

    try:
        r_del = client.delete(f"/api/platforms/{platform_id}")
        assert r_del.status_code in (200, 204)

        if r_del.status_code == 200:
            body = r_del.get_json()
            assert body["ok"] is True
            assert body["deleted_platform_id"] == platform_id
    finally:
        client.delete(f"/api/platforms/{platform_id}")
