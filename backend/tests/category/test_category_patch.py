
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


def test_patch_category(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- POST (create)
    r_post = client.post("/api/categories", json={"intitule": f"Categorie patch {uniq}"})
    assert r_post.status_code == 201
    created = r_post.get_json()
    cat_id = created["id"]

    try:
        # ---- PATCH
        r_patch = client.patch(f"/api/categories/{cat_id}", json={"intitule": f"Categorie patched {uniq}"})
        assert r_patch.status_code == 200

        patched = r_patch.get_json()
        assert patched["id"] == cat_id
        assert patched["intitule"] == f"Categorie patched {uniq}"
    finally:
        client.delete(f"/api/categories/{cat_id}")
