def test_delivery_companies_get_list(client):
    r = client.get("/api/delivery-companies")
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, list)


def test_delivery_company_get_by_id_not_found(client):
    r = client.get("/api/delivery-companies/99999999")
    assert r.status_code == 404
