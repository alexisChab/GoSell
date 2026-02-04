from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.App.db.base import Base

class DeliveryCompany(Base):
    __tablename__ = 'societe_livraison'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    frais_livraisons = relationship("frais_livraison", back_populates="societe_livraison", cascade="all, delete-orphan")


