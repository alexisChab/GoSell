import time
from tests.utils_auth import _register, _login


def _create_category(client, uniq: int) -> int:
    r_post_cat = client.post("/api/categories", json={"intitule": f"Categorie for genre {uniq}"})
    assert r_post_cat.status_code in (201, 409)

    # Si 409, ça veut dire que la catégorie existe déjà.
    # Comme on met uniq dans le nom, c’est très rare. Mais au cas où :
    if r_post_cat.status_code == 409:
        # On ne sait pas récupérer l'id via l'API sans endpoint de search,
        # donc on force un autre uniq (ou tu peux faire un GET list et chercher).
        raise AssertionError("Category already exists (409). Retry with another uniq.")

    return r_post_cat.get_json()["id"]


def test_patch_genre(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # Create category (FK required)
    cat_id = _create_category(client, uniq)

    # Create genre
    r_post = client.post(
        "/api/genres",
        json={"intitule": f"Genre patch {uniq}", "categorie_id": cat_id},
    )
    assert r_post.status_code in (201, 409)

    if r_post.status_code == 409:
        # cleanup catégorie (sinon fuite)
        client.delete(f"/api/categories/{cat_id}")
        return

    created = r_post.get_json()
    assert "id" in created
    genre_id = created["id"]

    try:
        # Patch
        patch_payload = {"intitule": f"Genre patched {uniq}"}
        r_patch = client.patch(f"/api/genres/{genre_id}", json=patch_payload)
        assert r_patch.status_code == 200

        patched = r_patch.get_json()
        assert patched["id"] == genre_id
        assert patched["intitule"] == f"Genre patched {uniq}"
    finally:
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
