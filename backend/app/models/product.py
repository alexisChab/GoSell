from sqlalchemy import ForeignKey, Integer,String, Boolean, Date, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from backend.app.db.base import Base

class Produit(Base):
    __tablename__ = 'produit'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    en_vente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    est_vendu: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    a_ete_achete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prix_achat: Mapped[float | None] = mapped_column(Float, nullable=True, default=0)
    prix_vente: Mapped[float|None] = mapped_column(Float, nullable=True)
    prix_min_espere: Mapped[Float |None] = mapped_column(Float, nullable=True, default=0)
    prix_max_espere: Mapped[float | None] = mapped_column(Float, nullable=True, default=0)
    date_mise_en_vente: Mapped[date | None ] = mapped_column(Date, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_app.id"), nullable=False)
    utilisateur = relationship("user_app", back_populates="produit")
    types_produit = relationship("type_produit", secondary="produit_type_produit", back_populates="produits")
    ou_ventes = relationship("ou_vente", back_populates="produit", cascade="all, delete-orphan")
    frais_annonces = relationship("frais_annexe", back_populates="produit", cascade="all, delete-orphan")
    frais_livraisons = relationship("frais_livraison", back_populates="produit", cascade="all, delete-orphan")