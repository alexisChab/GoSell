from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.App.db.base import Base

class DeliveryCharges(Base):
    __tablename__ = 'frais_livraison'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    montant: Mapped[float] = mapped_column(Float, primary_key=True, nullable=False)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produit.id"), nullable=False)
    produit = relationship("Produit", back_populates="frais_annexes")
    societe_id: Mapped[int] = mapped_column(ForeignKey("societe_livraison.id"), nullable=True)
