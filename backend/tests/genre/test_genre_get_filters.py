# tests/genre/test_genre_get_filters.py
from tests.utils_auth import _register, _login


def test_genres_get_list_with_filters(client):
    _register(client)
    _login(client)

    r = client.get(
        "/api/genres?"
        "search=test"
        "&page=1&page_size=20"
        "&order_by=intitule&order_dir=asc"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert isinstance(body, list)

