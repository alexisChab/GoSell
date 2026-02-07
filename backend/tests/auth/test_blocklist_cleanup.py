from app.models.token_blocklist import TokenBlocklist
from app.extensions import db
from tests.auth.helper_auth import login, logout_access

def test_logout_adds_token_to_blocklist(client, app):
    r = login(client, "alexis.test60@local.dev", "Test1234!")
    assert r.status_code == 200
    csrf_access = (r.get_json() or {}).get("csrf_access_token")

    # logout
    r2 = logout_access(client, csrf=csrf_access)
    assert r2.status_code in (200, 204)

    with app.app_context():
        count = db.session.query(TokenBlocklist).count()
        assert count >= 1
