from sqlalchemy import Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class LotProduit(Base):
    __tablename__ = "lot_produit"

    __table_args__ = (
        UniqueConstraint("lot_id", "produit_id", name="uq_lot_produit"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    lot_id: Mapped[int] = mapped_column(ForeignKey("lot.id", ondelete="CASCADE"), nullable=False)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produit.id", ondelete="CASCADE"), nullable=False)

    # utile si plusieurs unités identiques dans le lot
    quantite: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # allocation optionnelle du prix d'achat global du lot
    allocation_prix_achat: Mapped[float | None] = mapped_column(Float, nullable=True)

    # allocation optionnelle des frais (livraison + annexes)
    allocation_frais: Mapped[float | None] = mapped_column(Float, nullable=True)

    # information métier (manual, equal, weighted_expected, etc.)
    allocation_methode: Mapped[str | None] = mapped_column(nullable=True)

    # relations
    lot = relationship("Lot", back_populates="lot_produits")
    produit = relationship("Produit", back_populates="lot_produits")
