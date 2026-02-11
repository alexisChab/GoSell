# tests/utils_type_produit.py
import time


def create_category(client, uniq: int) -> int:
    r = client.post("/api/categories", json={"intitule": f"Categorie tmp {uniq}"})
    assert r.status_code in (201, 409)
    if r.status_code == 409:
        raise AssertionError("Category already exists (409). Retry uniq.")
    return r.get_json()["id"]


def create_genre(client, uniq: int, categorie_id: int) -> int:
    r = client.post("/api/genres", json={"intitule": f"Genre tmp {uniq}", "categorie_id": categorie_id})
    assert r.status_code in (201, 409)
    if r.status_code == 409:
        raise AssertionError("Genre already exists (409). Retry uniq.")
    return r.get_json()["id"]
