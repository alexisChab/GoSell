from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProduitTypeProduit(Base):
    __tablename__ = "produit_type_produit"

    # -------------------------
    # Clé primaire composite
    # -------------------------

    produit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("produit.id", ondelete="CASCADE"),
        primary_key=True,
    )

    type_produit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("type_produit.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # -------------------------
    # Relations
    # -------------------------

    produit = relationship(
        "Produit",
        back_populates="produit_type_produits",
    )

    type_produit = relationship(
        "ProductType",
        back_populates="produit_type_produits",
    )

    # -------------------------
    # Représentation
    # -------------------------

    def __repr__(self) -> str:
        return (
            f"<ProduitTypeProduit "
            f"produit_id={self.produit_id} "
            f"type_produit_id={self.type_produit_id}>"
        )
