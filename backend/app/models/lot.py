from sqlalchemy import Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base


class Lot(Base):
    __tablename__ = "lot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    utilisateur = relationship("User", back_populates="lots")

    titre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    prix_total_achat: Mapped[float] = mapped_column(Float, nullable=False)

    date_achat: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    frais_livraison = relationship(
        "DeliveryCharges",
        back_populates="lot",
        cascade="all, delete-orphan",
    )
    frais_annexe = relationship(
        "OtherCharges",
        back_populates="lot",
        cascade="all, delete-orphan",
    )

    lot_produits = relationship("LotProduit", back_populates="lot", cascade="all, delete-orphan")
