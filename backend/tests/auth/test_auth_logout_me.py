from tests.auth.helper_auth import login, logout_access, me

def test_me_fails_after_logout(client):
    r = login(client, "alexis.test60@local.dev", "Test1234!")
    assert r.status_code == 200

    data = r.get_json() or {}
    csrf_access = data.get("csrf_access_token")

    r2 = me(client)
    assert r2.status_code == 200
    assert "user" in (r2.get_json() or {})

    r3 = logout_access(client, csrf=csrf_access)
    assert r3.status_code in (200, 204)

    r4 = me(client)
    assert r4.status_code in (401, 422)
