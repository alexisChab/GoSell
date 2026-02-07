from datetime import datetime, timedelta
from app.extensions import db
from app.models.token_blocklist import TokenBlocklist
from app.crud.token_blocklist import cleanup_revoked_tokens
from uuid import uuid4

def test_cleanup_deletes_expired_tokens(app):
    with app.app_context():
        expired_jti = str(uuid4())
        valid_jti = str(uuid4())

        expired = TokenBlocklist(
            jti=expired_jti,
            token_type="access",
            revoked_at=datetime.utcnow() - timedelta(days=2),
            expires_at=datetime.utcnow() - timedelta(days=1),
            user_id=1,
        )

        valid = TokenBlocklist(
            jti=valid_jti,
            token_type="access",
            revoked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=1),
            user_id=1,
        )

        db.session.add_all([expired, valid])
        db.session.commit()

        deleted = cleanup_revoked_tokens()
        assert deleted >= 1

        remaining_jtis = [
            t.jti
            for t in db.session.query(TokenBlocklist)
            .filter(TokenBlocklist.jti.in_([expired_jti, valid_jti]))
            .all()
        ]

        assert expired_jti not in remaining_jtis
        assert valid_jti in remaining_jtis
