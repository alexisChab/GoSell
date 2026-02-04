from sqlalchemy import ForeignKey, Integer,String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

class Stock(Base):
    __tablename__ = 'stock'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    localisation: Mapped[str | None] = mapped_column(String, nullable=True)
    a_et_achete: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    type_produit_id: Mapped[int | None] = mapped_column(ForeignKey("type_produit.id"), nullable=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("user_app.id"), nullable=False)

    utilisateur = relationship("user_app", back_populates="stocks")
    type_produit = relationship("type_produits")