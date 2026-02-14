from tests.utils_auth import _register, _login


def test_delivery_charges_requires_auth(client):
    r = client.get("/api/frais-livraison")
    assert r.status_code in (401, 422)


def test_delivery_charges_get_list_when_logged_in(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get("/api/frais-livraison?page=1&page_size=20&order_by=id&order_dir=desc")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)
