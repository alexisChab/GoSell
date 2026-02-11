from sqlalchemy import Integer, String, ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class OtherCharges(Base):
    __tablename__ = 'frais_annexe'
    __table_args__ = (
        CheckConstraint(
            "(produit_id IS NOT NULL) <> (lot_id IS NOT NULL)",
            name="chk_frais_annexe_target",
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intitule: Mapped[str] = mapped_column(String, nullable=False)
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    produit_id: Mapped[int] = mapped_column(ForeignKey('produit.id'), nullable=True)
    produit = relationship("Produit", back_populates="frais_annexe")
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("lot.id"), nullable=True)
    lot = relationship("Lot", back_populates="frais_annexe")