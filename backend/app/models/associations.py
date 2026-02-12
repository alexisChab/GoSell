from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class CategorieGenre(Base):
    __tablename__ = "categorie_genre"
    categorie_id: Mapped[int] = mapped_column(ForeignKey("categorie.id"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genre.id"), primary_key=True)


