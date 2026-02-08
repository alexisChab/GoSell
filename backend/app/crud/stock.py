# app/crud/stock.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import select, and_, delete
from app.db.deps import db
from app.models.stock import Stock


class NotFoundError(Exception):
    pass


def get_stock_for_user(user_id: int, filters: dict):
    """
    Retourne la liste du stock de l'utilisateur connecté,
    avec filtres/pagination/tri appliqués.
    """
    session = db()

    conditions = [Stock.user_id == user_id]

    # ---- search sur nom
    if filters.get("search"):
        conditions.append(Stock.nom.ilike(f"%{filters['search']}%"))

    # ---- bool
    if filters.get("a_ete_achete") is not None:
        conditions.append(Stock.a_ete_achete == filters["a_ete_achete"])

    # ---- range prix_achat (Float)
    if filters.get("prix_achat_min") is not None:
        conditions.append(Stock.prix_achat >= filters["prix_achat_min"])
    if filters.get("prix_achat_max") is not None:
        conditions.append(Stock.prix_achat <= filters["prix_achat_max"])

    # ---- range created_at (DateTime)
    if filters.get("created_at_from") is not None:
        conditions.append(Stock.created_at >= filters["created_at_from"])
    if filters.get("created_at_to") is not None:
        conditions.append(Stock.created_at <= filters["created_at_to"])

    # ---- order by
    order_by = filters.get("order_by") or "created_at"
    order_dir = filters.get("order_dir", "desc")

    col = getattr(Stock, order_by, Stock.created_at)
    col = col.desc() if order_dir == "desc" else col.asc()

    # ---- pagination
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


def get_stock_item_for_user_by_id(user_id: int, stock_id: int) -> Stock:
    """
    Retourne un item stock par id, ownership enforced.
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

class NotFoundError(Exception):
    pass


def create_stock_item(user_id: int, data: dict) -> Stock:
    """
    Crée un item de stock appartenant à user_id.
    data vient de StockCreateSchema.load(...)
    """
    session = db()

    item = Stock(
        nom=data["nom"],
        description=data.get("description"),
        localisation=data.get("localisation"),
        a_ete_achete=data.get("a_ete_achete", False),
        prix_achat=data.get("prix_achat"),
        user_id=user_id,
        created_at=data.get("created_at") or datetime.utcnow(),
    )

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_stock_item(user_id: int, stock_id: int) -> None:
    """
    Supprime un item de stock si et seulement s'il appartient à user_id.
    Anti-leak: si pas trouvé (ou pas à lui) => NotFoundError.
    """
    session = db()

    stmt = delete(Stock).where(and_(Stock.id == stock_id, Stock.user_id == user_id))
    res = session.execute(stmt)
    session.commit()

    if res.rowcount == 0:
        raise NotFoundError("Stock introuvable")

def update_stock_item(user_id: int, stock_id: int, patch: dict) -> Stock:
    """
    Update partiel d'un item stock appartenant à user_id.
    patch vient de StockUpdateSchema.load(...).
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

    # Update uniquement des champs fournis
    for field, value in patch.items():
        setattr(item, field, value)

    session.commit()
    session.refresh(item)
    return item