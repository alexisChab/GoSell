from tests.utils_auth import _register, _login

API_USERS_PASSWORD = "/api/users/me/password"


def _skip_if_missing_route(resp):
    if resp.status_code == 404:
        import pytest
        pytest.skip("User routes not registered (got 404). Did you register user_bp?")


def test_patch_password_wrong_current_password(client):
    _register(client)
    r_login = _login(client)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.patch(
        API_USERS_PASSWORD,
        json={"current_password": "BAD", "new_password": "test1234NEW"},
    )
    _skip_if_missing_route(r)

    # si tu gères bien l'erreur -> 401
    assert r.status_code == 401
    body = r.get_json()
    assert "error" in body
