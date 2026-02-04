from sqlalchemy import Integer, String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.App.db.base import Base


class OtherCharges(Base):
    __tablename__ = 'frais_annexes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intitule: Mapped[str] = mapped_column(String, nullable=False)
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    produit_id: Mapped[int] = mapped_column(ForeignKey('produit.id'), nullable=False)