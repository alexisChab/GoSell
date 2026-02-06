from sqlalchemy import ForeignKey, Integer,String, Boolean, Date, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from app.db.base import Base

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
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    utilisateur = relationship("User", back_populates="produit")
    produit_type_produits = relationship(
        "ProduitTypeProduit",
        back_populates="produit",
        cascade="all, delete-orphan",
    )
    ou_vente = relationship("WhereSell", back_populates="produit", cascade="all, delete-orphan")
    frais_annexe = relationship("OtherCharges", back_populates="produit", cascade="all, delete-orphan")
    frais_livraison = relationship("DeliveryCharges", back_populates="produit", cascade="all, delete-orphan")

