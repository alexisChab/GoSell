import time
from tests.utils_auth import _register, _login


def _create_category(client, uniq: int) -> int:
    r_post_cat = client.post("/api/categories", json={"intitule": f"Categorie for genre {uniq}"})
    assert r_post_cat.status_code in (201, 409)

    if r_post_cat.status_code == 409:
        raise AssertionError("Category already exists (409). Retry with another uniq.")

    return r_post_cat.get_json()["id"]


def test_post_and_delete_genre(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # Create category (FK required)
    cat_id = _create_category(client, uniq)

    post_payload = {
        "intitule": f"Genre pytest {uniq}",
        "categorie_id": cat_id,
    }

    r_post = client.post("/api/genres", json=post_payload)
    assert r_post.status_code in (201, 409)

    if r_post.status_code == 409:
        client.delete(f"/api/categories/{cat_id}")
        return

    created = r_post.get_json()
    assert "id" in created
    genre_id = created["id"]

    try:
        r_del = client.delete(f"/api/genres/{genre_id}")
        assert r_del.status_code in (200, 204)

        if r_del.status_code == 200:
            body = r_del.get_json()
            assert body["ok"] is True
            assert body["deleted_genre_id"] == genre_id
    finally:
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
