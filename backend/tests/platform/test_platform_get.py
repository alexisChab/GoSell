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

def test_platforms_get_list(client):
    _register(client)
    _login(client)
    r = client.get("/api/platforms")
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, list)


def test_platforms_get_list_with_filters(client):
    _register(client)
    _login(client)
    r = client.get(
        "/api/platforms?"
        "search=test"
        "&frais_supp_eur_min=0"
        "&frais_supp_eur_max=100"
        "&pourcentage_vente_min=0"
        "&pourcentage_vente_max=50"
        "&order_by=nom&order_dir=asc"
        "&page=1&page_size=20"
    )
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, list)


def test_platform_get_by_id_not_found(client):
    _register(client)
    _login(client)
    # id volontairement improbable
    r = client.get("/api/platforms/99999999")
    assert r.status_code == 404
