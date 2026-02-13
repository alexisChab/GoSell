from tests.utils_auth import _register, _login


def test_lot_get_by_id_not_found(client):
    _register(client)
    _login(client)

    r = client.get("/api/lots/99999999")
    assert r.status_code == 404
    body = r.get_json()
    assert body["ok"] is False
