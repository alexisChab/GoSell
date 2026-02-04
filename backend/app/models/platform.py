from sqlalchemy import ForeignKey, Integer,String, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

class Platform(Base):
    __tablename__ = 'platforme'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    frais_supp_eur: Mapped[float | None] = mapped_column(Float, nullable=True, default=0)
    pourcentage_vente: Mapped[float | None] = mapped_column(Float, nullable=True, default=0)
    lien_homepage: Mapped[str | None] = mapped_column(String, nullable=True)
    ou_vente = relationship("ou_vente", back_populates="plateforme", cascade="all, delete-orphan")
