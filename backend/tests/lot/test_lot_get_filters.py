import time
from tests.utils_auth import _register, _login


def test_lots_get_list_with_filters(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())
    lot1_id = None
    lot2_id = None

    # On crée 2 lots avec dates + prix différents pour tester les filtres
    try:
        r1 = client.post(
            "/api/lots",
            json={
                "titre": f"Lot filt A {uniq}",
                "prix_total_achat": 10.0,
                "date_achat": "2026-02-10T10:00:00",
            },
        )
        assert r1.status_code == 201
        lot1_id = r1.get_json()["id"]

        r2 = client.post(
            "/api/lots",
            json={
                "titre": f"Lot filt B {uniq}",
                "prix_total_achat": 200.0,
                "date_achat": "2026-02-12T10:00:00",
            },
        )
        assert r2.status_code == 201
        lot2_id = r2.get_json()["id"]

        # Filtre prix_min (doit contenir B, pas A)
        r = client.get(
            "/api/lots?"
            "prix_min=100"
            "&page=1&page_size=50"
            "&order_by=prix_total_achat&order_dir=asc"
        )
        assert r.status_code == 200
        body = r.get_json()
        ids = {x["id"] for x in body}
        assert lot2_id in ids
        assert lot1_id not in ids

        # Filtre date_min/date_max (ne doit contenir que B)
        r = client.get(
            "/api/lots?"
            "date_min=2026-02-11T00:00:00"
            "&date_max=2026-02-13T00:00:00"
            "&page=1&page_size=50"
            "&order_by=date_achat&order_dir=asc"
        )
        assert r.status_code == 200
        body = r.get_json()
        ids = {x["id"] for x in body}
        assert lot2_id in ids
        assert lot1_id not in ids

        # Filtre prix_max (doit contenir A, pas B)
        r = client.get("/api/lots?prix_max=50&page=1&page_size=50")
        assert r.status_code == 200
        body = r.get_json()
        ids = {x["id"] for x in body}
        assert lot1_id in ids
        assert lot2_id not in ids

    finally:
        # cleanup
        if lot1_id is not None:
            client.delete(f"/api/lots/{lot1_id}")
        if lot2_id is not None:
            client.delete(f"/api/lots/{lot2_id}")
