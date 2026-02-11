from sqlalchemy import Integer,String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Category(Base):
    __tablename__ = 'categorie'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intitule: Mapped[str] = mapped_column(String, nullable=False)
    genres = relationship(
        "Genre",
        back_populates="categorie",
        cascade="all, delete-orphan",
    )
