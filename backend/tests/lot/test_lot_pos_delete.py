import time
from tests.utils_auth import _register, _login


def test_post_patch_get_and_delete_lot(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    uniq = int(time.time())
    lot_id = None

    try:
        # CREATE
        r_post = client.post(
            "/api/lots",
            json={
                "titre": f"Lot pytest {uniq}",
                "description": "test lot create",
                "prix_total_achat": 123.45,
                "date_achat": "2026-02-11T12:00:00",
            },
        )
        assert r_post.status_code == 201
        created = r_post.get_json()
        lot_id = created["id"]

        # GET by id
        r_get = client.get(f"/api/lots/{lot_id}")
        assert r_get.status_code == 200
        got = r_get.get_json()
        assert got["id"] == lot_id
        assert got["prix_total_achat"] == 123.45

        # PATCH
        r_patch = client.patch(
            f"/api/lots/{lot_id}",
            json={"titre": f"Lot updated {uniq}", "prix_total_achat": 99.99},
        )
        assert r_patch.status_code == 200
        patched = r_patch.get_json()
        assert patched["id"] == lot_id
        assert patched["titre"] == f"Lot updated {uniq}"
        assert patched["prix_total_achat"] == 99.99

        # PATCH vide -> 400 (si tu as gardé NO_FIELDS_TO_PATCH)
        r_patch_empty = client.patch(f"/api/lots/{lot_id}", json={})
        assert r_patch_empty.status_code == 400

        # DELETE
        r_del = client.delete(f"/api/lots/{lot_id}")
        assert r_del.status_code in (200, 204)

        # GET after delete -> 404
        r_get2 = client.get(f"/api/lots/{lot_id}")
        assert r_get2.status_code == 404

    finally:
        # cleanup idempotent
        if lot_id is not None:
            client.delete(f"/api/lots/{lot_id}")
