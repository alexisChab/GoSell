from datetime import datetime, timezone
from sqlalchemy import select

from app.db.deps import db
from app.models.token_blocklist import TokenBlocklist


def revoke_token(*, jti: str, token_type: str, user_id: int, expires_at):
    token = TokenBlocklist(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        expires_at=expires_at,
    )
    session = db()
    session.add(token)
    session.commit()


def is_token_revoked(jti: str) -> bool:
    session = db()
    stmt = select(TokenBlocklist).where(
        TokenBlocklist.jti == jti,
        TokenBlocklist.expires_at > datetime.now(timezone.utc),
    )
    return session.execute(stmt).scalar_one_or_none() is not None
