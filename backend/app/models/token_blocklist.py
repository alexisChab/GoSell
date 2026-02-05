from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    token_type: Mapped[str] = mapped_column(String(10), nullable=False)  # access / refresh
    user_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id"), nullable=False, index=True)

    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
