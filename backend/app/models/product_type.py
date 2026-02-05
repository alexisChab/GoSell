from sqlalchemy import ForeignKey, Integer,String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ProductType(Base):
    __tablename__ = 'type_produit'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    categorie_id: Mapped[int] = mapped_column(ForeignKey("categorie.id"), nullable=False)
    categorie = relationship("Category", back_populates="types_produit")
    produit_type_produits = relationship(
        "ProduitTypeProduit",
        back_populates="type_produit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("categorie_id", "nom", name="uq_typeproduit_par_categorie"),)