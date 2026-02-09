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


def test_patch_platform(client):
    # register (ok si déjà existant)
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    # login (cookies JWT)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- POST /api/platforms (auth required)
    post_payload = {
        "nom": f"Plateforme pytest patch {uniq}",
        "frais_supp_eur": 1.5,
        "pourcentage_vente": 5.0,
        "lien_homepage": "https://example.com",
    }

    r_post = client.post("/api/platforms", json=post_payload)
    assert r_post.status_code == 201

    created = r_post.get_json()
    assert "id" in created
    platform_id = created["id"]

    try:
        # ---- PATCH /api/platforms/<id>
        patch_payload = {
            "frais_supp_eur": 2.0,
            "pourcentage_vente": 7.5,
            "lien_homepage": "https://example.org",
        }

        r_patch = client.patch(f"/api/platforms/{platform_id}", json=patch_payload)
        assert r_patch.status_code == 200

        patched = r_patch.get_json()
        assert patched["id"] == platform_id
        assert float(patched["frais_supp_eur"]) == 2.0
        assert float(patched["pourcentage_vente"]) == 7.5
        assert patched["lien_homepage"] == "https://example.org"

    finally:
        # cleanup
        client.delete(f"/api/platforms/{platform_id}")
