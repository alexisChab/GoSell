# tests/utils_product.py
def create_product(client, uniq: int) -> int:
    payload = {
        "nom": f"Produit pivot {uniq}",
        "description": "test pivot",
    }
    r = client.post("/api/products", json=payload)
    assert r.status_code == 201
    return r.get_json()["id"]
