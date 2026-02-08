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


def test_stock_requires_auth(client):
    r = client.get("/api/stock")
    # JWT cookies manquants => 401/422 selon config
    assert r.status_code in (401, 422)


def test_stock_get_list_when_logged_in(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    # sanity check
    r_me = client.get("/api/auth/me")
    assert r_me.status_code == 200

    r = client.get("/api/stock")
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, list)


def test_stock_get_list_with_filters(client):
    _register(client)
    _login(client)

    # Même si aucun item en stock, ça doit répondre 200 + liste
    r = client.get(
        "/api/stock?"
        "search=test"
        "&a_ete_achete=false"
        "&prix_achat_min=0&prix_achat_max=999999"
        "&order_by=created_at&order_dir=desc"
        "&page=1&page_size=20"
    )
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
