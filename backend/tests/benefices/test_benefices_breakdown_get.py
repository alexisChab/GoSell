from utils_auth import _register, _login


def test_benefices_breakdown_requires_auth(client):
    r = client.get("/api/benefices/breakdown?group_by=categorie")
    assert r.status_code in (401, 422)


def _assert_payload(data: dict):
    assert "group_by" in data
    assert "items" in data and isinstance(data["items"], list)
    assert "count" in data and data["count"] == len(data["items"])
    if data["items"]:
        it = data["items"][0]
        for k in (
            "group_id",
            "group_name",
            "count_products",
            "revenue_expected_median",
            "cost_products",
            "fees",
            "cost_total",
            "profit_expected_median",
            "is_profit_expected_median",
            "avg_multiple_median",
        ):
            assert k in it


def test_benefices_breakdown_ok_by_categorie(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices/breakdown?group_by=categorie&limit=20&min_count=1")
    assert r.status_code == 200
    data = r.get_json()
    _assert_payload(data)
    assert data["group_by"] == "categorie"


def test_benefices_breakdown_ok_by_genre(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices/breakdown?group_by=genre&limit=20&min_count=1")
    assert r.status_code == 200
    data = r.get_json()
    _assert_payload(data)
    assert data["group_by"] == "genre"


def test_benefices_breakdown_ok_by_type(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices/breakdown?group_by=type_produit&limit=20&min_count=1")
    assert r.status_code == 200
    data = r.get_json()
    _assert_payload(data)
    assert data["group_by"] == "type_produit"


def test_benefices_breakdown_validation(client):
    r_reg = _register(client)
    assert r_reg.status_code in (201, 409)
    r_login = _login(client)
    assert r_login.status_code == 200

    r = client.get("/api/benefices/breakdown?group_by=invalid")
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"