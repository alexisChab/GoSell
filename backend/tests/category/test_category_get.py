def test_categories_get_list(client):
    r = client.get("/api/categories")
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, list)


def test_category_get_by_id_not_found(client):
    r = client.get("/api/categories/99999999")
    assert r.status_code == 404
