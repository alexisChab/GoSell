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


def test_products_requires_auth(client):
    r = client.get("/api/products")
    assert r.status_code in (401, 422)


def test_products_get_list_when_logged_in(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    body = r_login.get_json()
    assert body["ok"] is True


    r_me = client.get("/api/auth/me")
    assert r_me.status_code == 200

    r = client.get("/api/products")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_products_get_list_with_filters(client):
    _register(client)
    _login(client)

    r = client.get("/api/products?en_vente=true&prix_vente_min=10&prix_vente_max=200&page=1&page_size=20")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
