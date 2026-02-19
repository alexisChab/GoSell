from utils_auth import _register, _login


def test_best_types_requires_auth(client):
    r = client.get("/api/best-types")
    assert r.status_code in (401, 422)


def test_best_types_ok(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/best-types?min_multiple=1.5&min_count=1&limit=20")
    assert r.status_code == 200
    data = r.get_json()

    assert "filters" in data
    assert "items" in data and isinstance(data["items"], list)
    assert "count" in data and data["count"] == len(data["items"])

    if data["items"]:
        it = data["items"][0]
        for k in ("type_produit_id", "count_products", "avg_multiple_median", "success_rate", "avg_cost_total"):
            assert k in it