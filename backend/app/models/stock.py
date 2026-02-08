from sqlalchemy import ForeignKey, Integer,String, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

class Stock(Base):
    __tablename__ = 'stock'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    localisation: Mapped[str | None] = mapped_column(String, nullable=True)
    a_ete_achete: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    prix_achat: Mapped[float] = mapped_column(Float,nullable=True)
    utilisateur = relationship("User", back_populates="stock")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)