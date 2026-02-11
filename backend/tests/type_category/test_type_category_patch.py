import time
from tests.utils_auth import _register, _login
from tests.utils_type_produit import create_category, create_genre


def test_patch_type_produit(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- create dependencies
    cat_id = create_category(client, uniq)
    genre_id = create_genre(client, uniq, cat_id)

    # ---- POST create
    r_post = client.post("/api/type-produits", json={"nom": f"TypeProduit patch {uniq}", "genre_id": genre_id})
    assert r_post.status_code in (201, 409)

    if r_post.status_code == 409:
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
        return

    created = r_post.get_json()
    type_id = created["id"]

    try:
        # ---- PATCH
        r_patch = client.patch(f"/api/type-produits/{type_id}", json={"nom": f"TypeProduit patched {uniq}"})
        assert r_patch.status_code == 200

        patched = r_patch.get_json()
        assert patched["id"] == type_id
        assert patched["nom"] == f"TypeProduit patched {uniq}"
        assert patched["genre_id"] == genre_id
    finally:
        client.delete(f"/api/type-produits/{type_id}")
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
