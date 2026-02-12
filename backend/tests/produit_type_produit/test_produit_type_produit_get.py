from tests.utils_auth import _register, _login


def test_produit_type_produits_requires_auth(client):
    r = client.get("/api/produit-type-produits")
    assert r.status_code in (401, 422)


def test_produit_type_produits_get_list_when_logged_in(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/produit-type-produits?page=1&page_size=20")
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)
