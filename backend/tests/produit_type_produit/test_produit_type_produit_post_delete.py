import time
from tests.utils_auth import _register, _login

# crée ce helper en recopiant le payload exact qui marche déjà dans tes tests produits
from tests.utils_product import create_product


def test_post_get_and_delete_produit_type_produit(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())

    # category
    r_cat = client.post("/api/categories", json={"intitule": f"Categorie p2p {uniq}"})
    assert r_cat.status_code == 201
    cat_id = r_cat.get_json()["id"]

    # genre (FK categorie)
    r_genre = client.post("/api/genres", json={"intitule": f"Genre p2p {uniq}", "categorie_id": cat_id})
    assert r_genre.status_code == 201
    genre_id = r_genre.get_json()["id"]

    # type_produit (FK genre)
    r_tp = client.post("/api/type-produits", json={"nom": f"TypeProduit p2p {uniq}", "genre_id": genre_id})
    assert r_tp.status_code == 201
    type_produit_id = r_tp.get_json()["id"]

    # product (route réelle = /api/products)
    produit_id = create_product(client, uniq)

    # link
    r_link = client.post(
        "/api/produit-type-produits",
        json={"produit_id": produit_id, "type_produit_id": type_produit_id},
    )
    assert r_link.status_code in (201, 409)

    # get link
    r_get = client.get(f"/api/produit-type-produits/{produit_id}/{type_produit_id}")
    assert r_get.status_code == 200
    got = r_get.get_json()
    assert got["produit_id"] == produit_id
    assert got["type_produit_id"] == type_produit_id

    # delete link
    r_del = client.delete(f"/api/produit-type-produits/{produit_id}/{type_produit_id}")
    assert r_del.status_code in (200, 204)

    # cleanup
    try:
        client.delete(f"/api/produit-type-produits/{produit_id}/{type_produit_id}")
    finally:
        client.delete(f"/api/products/{produit_id}")
        client.delete(f"/api/type-produits/{type_produit_id}")
        client.delete(f"/api/genres/{genre_id}")
        client.delete(f"/api/categories/{cat_id}")
