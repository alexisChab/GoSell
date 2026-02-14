import time
from tests.utils_auth import _register, _login

API_USERS_ME = "/api/users/me"
API_USERS_PASSWORD = "/api/users/me/password"


def test_users_me_requires_auth(client):
    r = client.get(API_USERS_ME)
    assert r.status_code in (401, 422)


def test_get_me_when_logged_in(client):
    uniq = int(time.time())
    email = f"user.me.{uniq}@local.dev"
    password = "Test1234!"

    r_reg = _register(client, email=email, password=password)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client, email=email, password=password)
    assert r_login.status_code == 200
    assert r_login.get_json()["ok"] is True

    r = client.get(API_USERS_ME)
    assert r.status_code == 200
    body = r.get_json()
    assert body["user"]["email"] == email


def test_patch_me_updates_profile(client):
    uniq = int(time.time())
    email = f"user.patch.{uniq}@local.dev"
    password = "Test1234!"

    r_reg = _register(client, email=email, password=password)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client, email=email, password=password)
    assert r_login.status_code == 200

    r_patch = client.patch(
        API_USERS_ME,
        json={"name": "New Name pytest", "username": f"pytest_{uniq}"},
    )
    assert r_patch.status_code == 200
    user = r_patch.get_json()["user"]
    assert user["name"] == "New Name pytest"
    assert user["username"] == f"pytest_{uniq}"


def test_patch_me_email_conflict(client):
    uniq = int(time.time())
    password = "Test1234!"

    email_a = f"user.a.{uniq}@local.dev"
    email_b = f"user.b.{uniq}@local.dev"

    # user A
    r_reg_a = _register(client, email=email_a, password=password)
    assert r_reg_a.status_code in (201, 409)

    # user B
    r_reg_b = _register(client, email=email_b, password=password)
    assert r_reg_b.status_code in (201, 409)

    # login user A
    r_login_a = _login(client, email=email_a, password=password)
    assert r_login_a.status_code == 200

    # try set email to email_b => conflict
    r_patch = client.patch(API_USERS_ME, json={"email": email_b})
    assert r_patch.status_code == 409
    assert r_patch.get_json()["error"]["code"] == "CONFLICT"


def test_patch_password_then_login_with_new_password(client):
    uniq = int(time.time())
    email = f"user.pwd.{uniq}@local.dev"
    old_password = "Test1234!"
    new_password = "Test1234!NEW"

    r_reg = _register(client, email=email, password=old_password)
    assert r_reg.status_code in (201, 409)

    r_login = _login(client, email=email, password=old_password)
    assert r_login.status_code == 200

    r_pwd = client.patch(
        API_USERS_PASSWORD,
        json={"current_password": old_password, "new_password": new_password},
    )
    assert r_pwd.status_code == 200
    assert r_pwd.get_json()["ok"] is True

    # re-login with new password
    r_login2 = _login(client, email=email, password=new_password)
    assert r_login2.status_code == 200
    assert r_login2.get_json()["ok"] is True
