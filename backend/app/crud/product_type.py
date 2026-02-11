# app/crud/product_type.py
from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db  # db() -> Session (via flask.g.db)
from app.models.product_type import ProductType


# ---------- GET LIST (filtres / tri / pagination) ----------

ALLOWED_ORDER_BY = {"id", "nom", "genre_id"}


def get_product_types(filters: dict) -> list[ProductType]:
    session: Session = db()

    conditions = []

    # filtres
    if filters.get("genre_id") is not None:
        conditions.append(ProductType.genre_id == filters["genre_id"])

    if filters.get("search"):
        conditions.append(ProductType.nom.ilike(f"%{filters['search']}%"))

    # tri
    order_by = (filters.get("order_by") or "id").strip()
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "id"

    order_dir = (filters.get("order_dir") or "desc").lower()
    col = getattr(ProductType, order_by, ProductType.id)
    col = col.desc() if order_dir == "desc" else col.asc()

    # pagination
    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size

    stmt = select(ProductType).order_by(col).offset(offset).limit(page_size)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    return session.execute(stmt).scalars().all()


# ---------- GET BY ID ----------

def get_product_type_by_id(type_id: int) -> ProductType | None:
    session: Session = db()
    return session.get(ProductType, type_id)


# ---------- CREATE ----------

def create_product_type(nom: str, genre_id: int) -> ProductType:
    session: Session = db()

    item = ProductType(nom=nom, genre_id=genre_id)
    session.add(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # - unique (genre_id, nom)
        # - FK genre_id invalide
        raise

    session.refresh(item)
    return item


# ---------- PATCH ----------

def patch_product_type(type_id: int, data: dict) -> ProductType | None:
    session: Session = db()

    item: ProductType | None = session.get(ProductType, type_id)
    if item is None:
        return None

    if "nom" in data:
        item.nom = data["nom"]
    if "genre_id" in data:
        item.genre_id = data["genre_id"]

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# ---------- DELETE ----------

def delete_product_type(type_id: int) -> bool:
    session: Session = db()

    item: ProductType | None = session.get(ProductType, type_id)
    if item is None:
        return False

    session.delete(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # ex: type_produit encore référencé dans la table pivot produit_type_produit
        raise

    return True
