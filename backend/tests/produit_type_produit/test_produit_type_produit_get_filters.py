import time
from tests.utils_auth import _register, _login
from tests.utils_product import create_product


def test_produit_type_produits_get_list_with_filters(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    r_cat = client.post("/api/categories", json={"intitule": f"Categorie p2p filt {uniq}"})
    assert r_cat.status_code == 201
    cat_id = r_cat.get_json()["id"]

    r_genre = client.post("/api/genres", json={"intitule": f"Genre p2p filt {uniq}", "categorie_id": cat_id})
    assert r_genre.status_code == 201
    genre_id = r_genre.get_json()["id"]

    r_tp = client.post("/api/type-produits", json={"nom": f"TypeProduit p2p filt {uniq}", "genre_id": genre_id})
    assert r_tp.status_code == 201
    type_produit_id = r_tp.get_json()["id"]

    produit_id = create_product(client, uniq)

    r_link = client.post(
        "/api/produit-type-produits",
        json={"produit_id": produit_id, "type_produit_id": type_produit_id},
    )
    assert r_link.status_code in (201, 409)

    r = client.get(f"/api/produit-type-produits?produit_id={produit_id}&page=1&page_size=20")
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)
    assert any(x["produit_id"] == produit_id and x["type_produit_id"] == type_produit_id for x in body)

    # cleanup
    try:
        client.delete(f"/api/produit-type-produits/{produit_id}/{type_produit_id}")
    finally:
        client.delete(f"/api/products/{produit_id}")
        client.delete(f"/api/type-produits/{type_produit_id}")
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
