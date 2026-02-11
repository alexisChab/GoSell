from tests.utils_auth import _register, _login


def test_type_produits_requires_auth(client):
    r = client.get("/api/type-produits")
    assert r.status_code in (401, 422)


def test_type_produits_get_list_when_logged_in(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/type-produits?page=1&page_size=20&order_by=id&order_dir=desc")
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)


def test_type_produit_get_by_id_not_found(client):
    _register(client)
    _login(client)

    r = client.get("/api/type-produits/99999999")
    assert r.status_code == 404
    body = r.get_json(silent=True) or {}
    assert body.get("ok") is False
