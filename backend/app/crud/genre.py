# app/crud/genre.py
from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.db.deps import db  # db() -> Session (via flask.g.db)
from app.models.genre import Genre


# ---------- GET LIST (avec filtres / tri / pagination) ----------

ALLOWED_ORDER_BY = {"id", "intitule", "categorie_id"}


def get_genres(filters: dict) -> list[Genre]:
    session: Session = db()

    conditions = []

    # filtres
    if filters.get("categorie_id") is not None:
        conditions.append(Genre.categorie_id == filters["categorie_id"])

    if filters.get("search"):
        conditions.append(Genre.intitule.ilike(f"%{filters['search']}%"))

    # tri
    order_by = (filters.get("order_by") or "id").strip()
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "id"

    order_dir = (filters.get("order_dir") or "desc").lower()
    col = getattr(Genre, order_by, Genre.id)
    col = col.desc() if order_dir == "desc" else col.asc()

    # pagination
    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size

    stmt = select(Genre).order_by(col).offset(offset).limit(page_size)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    return session.execute(stmt).scalars().all()


# ---------- GET BY ID ----------

def get_genre_by_id(genre_id: int) -> Genre | None:
    session: Session = db()
    return session.get(Genre, genre_id)


# ---------- CREATE ----------

def create_genre(intitule: str, categorie_id: int) -> Genre:
    session: Session = db()

    item = Genre(intitule=intitule, categorie_id=categorie_id)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


# ---------- PATCH ----------

def patch_genre(genre_id: int, data: dict) -> Genre | None:
    session: Session = db()

    item: Genre | None = session.get(Genre, genre_id)
    if item is None:
        return None

    # champs patchables
    if "intitule" in data:
        item.intitule = data["intitule"]
    if "categorie_id" in data:
        item.categorie_id = data["categorie_id"]

    session.commit()
    session.refresh(item)
    return item


# ---------- DELETE ----------

def delete_genre(genre_id: int) -> bool:
    session: Session = db()

    item: Genre | None = session.get(Genre, genre_id)
    if item is None:
        return False

    session.delete(item)
    session.commit()
    return True
