from tests.utils_auth import _register, _login


def test_where_sells_requires_auth(client):
    r = client.get("/api/ou-ventes")
    assert r.status_code in (401, 422)


def test_where_sells_get_list_when_logged_in(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/ou-ventes?page=1&page_size=20")
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)
