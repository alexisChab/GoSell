from sqlalchemy import Integer,String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class Category(Base):
    __tablename__ = 'categorie'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intitule: Mapped[str] = mapped_column(String, nullable=False)
    types_produit = relationship("TypeProduit", back_populates="categorie", cascade="all, delete-orphan")
    genres = relationship("genre", secondary="categorie_genre", back_populates="categories")