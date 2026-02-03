from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.App.db.base import Base

class CategorieGenre(Base):
    __tablename__ = "categorie_genre"
    categorie_id: Mapped[int] = mapped_column(ForeignKey("categorie.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genre.id"), primary_key=True)

class ProduitTypeProduit(Base):
    __tablename__ = "produit_type_produit"
    produit_id: Mapped[int] = mapped_column(ForeignKey("produit.id"), primary_key=True)
    type_produit_id: Mapped[int] = mapped_column(ForeignKey("type_produit.id"), primary_key=True)
