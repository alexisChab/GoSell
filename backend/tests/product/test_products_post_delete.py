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


def test_post_and_delete_product(client):
    # --------
    # Register (ok si déjà existant)
    # --------
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    # --------
    # Login (pose les cookies JWT)
    # --------
    r_login = _login(client)
    assert r_login.status_code == 200
    body = r_login.get_json()
    assert body["ok"] is True

    # --------
    # POST /products
    # --------
    product_payload = {
        "nom": "Produit pytest",
        "description": "Produit temporaire pour test",
        "prix_achat": 10,
        "prix_vente": 25,
        "en_vente": True,
    }

    r_post = client.post("/api/products", json=product_payload)
    assert r_post.status_code == 201

    product = r_post.get_json()
    assert product["nom"] == "Produit pytest"
    assert "id" in product

    product_id = product["id"]

    # --------
    # DELETE /products/<id>
    # --------
    r_delete = client.delete(f"/api/products/{product_id}")
    assert r_delete.status_code == 200

    delete_body = r_delete.get_json()
    assert delete_body["ok"] is True
    assert delete_body["deleted_product_id"] == product_id
