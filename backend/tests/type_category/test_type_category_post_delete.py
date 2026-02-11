import time
from tests.utils_auth import _register, _login
from tests.utils_type_produit import create_category, create_genre


def test_post_and_delete_type_produit(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # ---- create dependencies
    cat_id = create_category(client, uniq)
    genre_id = create_genre(client, uniq, cat_id)

    # ---- POST type_produit
    r_post = client.post("/api/type-produits", json={"nom": f"TypeProduit pytest {uniq}", "genre_id": genre_id})
    assert r_post.status_code in (201, 409)

    if r_post.status_code == 409:
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
        return

    created = r_post.get_json()
    type_id = created["id"]

    try:
        r_del = client.delete(f"/api/type-produits/{type_id}")
        assert r_del.status_code in (200, 204)
        if r_del.status_code == 200:
            body = r_del.get_json()
            assert body["ok"] is True
            assert body["deleted_type_produit_id"] == type_id
    finally:
        client.delete(f"/api/type-produits/{type_id}")
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
