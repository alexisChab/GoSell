from sqlalchemy import Integer,String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
class User(Base) :
    __tablename__ = 'app_user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    pro: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    produit = relationship("Produit", cascade="all, delete-orphan")
    stock = relationship("Stock", cascade="all, delete-orphan")
    lots = relationship("Lot", back_populates="utilisateur", cascade="all, delete-orphan")


