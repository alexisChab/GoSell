from tests.utils_auth import _register, _login


def test_type_produits_get_list_with_filters(client):
    _register(client)
    _login(client)

    r = client.get(
        "/api/type-produits?"
        "search=test"
        "&page=1&page_size=20"
        "&order_by=nom&order_dir=asc"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)
