# app/crud/stock.py
from __future__ import annotations

from sqlalchemy import select, and_
from app.db.deps import db
from app.models.stock import Stock


class NotFoundError(Exception):
    pass


def get_stock_for_user(user_id: int, filters: dict):
    """
    Liste le stock de l'utilisateur connecté avec filtres / tri / pagination.
    """
    session = db()

    conditions = [Stock.user_id == user_id]


    if filters.get("search"):
        conditions.append(Stock.nom.ilike(f"%{filters['search']}%"))


    def add_range(col, min_key, max_key):
        if filters.get(min_key) is not None:
            conditions.append(col >= filters[min_key])
        if filters.get(max_key) is not None:
            conditions.append(col <= filters[max_key])

    if hasattr(Stock, "prix_achat"):
        add_range(Stock.prix_achat, "prix_achat_min", "prix_achat_max")

    if hasattr(Stock, "valeur_estimee"):
        add_range(Stock.valeur_estimee, "valeur_estimee_min", "valeur_estimee_max")

    if filters.get("date_entree_from") is not None:
        conditions.append(Stock.created_at >= filters["date_entree_from"])

    if filters.get("date_entree_to") is not None:
        conditions.append(Stock.created_at <= filters["date_entree_to"])


    order_by = filters.get("order_by") or "created_at"
    order_dir = filters.get("order_dir", "desc")

    col = getattr(Stock, order_by, Stock.created_at)
    col = col.desc() if order_dir == "desc" else col.asc()

    page = filters.get("page", 1)
    page_size = filters.get("page_size", 20)
    offset = (page - 1) * page_size

    stmt = (
        select(Stock)
        .where(and_(*conditions))
        .order_by(col)
        .offset(offset)
        .limit(page_size)
    )

    return session.execute(stmt).scalars().all()


def get_stock_item_for_user_by_id(user_id: int, stock_id: int):
    """
    Détail d'un item stock (ownership enforced).
    """
    session = db()

    stmt = select(Stock).where(
        and_(
            Stock.id == stock_id,
            Stock.user_id == user_id,
        )
    )
    item = session.execute(stmt).scalars().first()

    if not item:
        raise NotFoundError("Stock introuvable")

    return item
