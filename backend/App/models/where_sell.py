from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.App.db.base import Base

class Where_Sell(Base):
    __tablename__ = 'ou_vente'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lien: Mapped[str |None] = mapped_column(String, nullable=True)
    plateforme_id: Mapped[int] = mapped_column(ForeignKey('plateforme.id'),primary_key=True)
    produit = relationship("Produit", back_populates="ou_ventes")
    plateforme = relationship("Plateforme", back_populates="ou_ventes")
