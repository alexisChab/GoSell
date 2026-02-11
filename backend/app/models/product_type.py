# app/models/product_type.py
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductType(Base):
    __tablename__ = "type_produit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)

    genre_id: Mapped[int] = mapped_column(ForeignKey("genre.id"), nullable=False)
    genre = relationship("Genre", back_populates="types_produit")

    produit_type_produits = relationship(
        "ProduitTypeProduit",
        back_populates="type_produit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("genre_id", "nom", name="uq_type_produit_genre_nom"),
    )
