from datetime import datetime, timezone
from sqlalchemy import select

from app.db.deps import db
from app.models import TokenBlocklist

def is_token_revoked(jti: str) -> bool:
    return db().execute(
        select(TokenBlocklist.id).where(TokenBlocklist.jti == jti)
    ).first() is not None

def revoke_token(*, jti: str, token_type: str, user_id: int, expires_at: datetime) -> None:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    db().add(TokenBlocklist(
        jti=jti,
        token_type=token_type,
        user_id=user_id,
        revoked_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    ))
    db().flush()
