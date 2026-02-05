from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class WhereSell(Base):
    __tablename__ = 'ou_vente'
    prodtui_id: Mapped[int] = mapped_column(ForeignKey("produit.id"), primary_key=True)
    lien: Mapped[str |None] = mapped_column(String, nullable=True)
    plateforme_id: Mapped[int] = mapped_column(ForeignKey('plateforme.id'), primary_key=True)
    produit = relationship("Produit", back_populates="ou_vente")
    plateforme = relationship("Platform", back_populates="ou_vente")
