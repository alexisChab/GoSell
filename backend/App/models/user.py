from sqlalchemy import Integer,String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.App.db.base import Base
class user(Base) :
    __tablename__ = 'app_user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    pro: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    produits = relationship("Produit", back_populates="utilisateur", cascade="all, delete-orphan")
    stock = relationship("Stock", back_populates="utilisateur", cascade="all, delete-orphan")

