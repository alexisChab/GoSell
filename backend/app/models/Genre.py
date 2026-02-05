from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Genre(Base):
    __tablename__ = 'genre'
    id: Mapped[int]= mapped_column(Integer, primary_key=True, autoincrement=True)
    intitule: Mapped[str] = mapped_column(String, nullable=False)
    categorie_id: Mapped[int]= mapped_column(Integer, ForeignKey('categorie.id'))
    categories = relationship("Category", secondary="categorie_genre", back_populates="genres")