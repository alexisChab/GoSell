from __future__ import annotations

from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.lot import Lot


# =========================================================
# GET LIST (scopé par user + filtres + pagination + tri)
# =========================================================

def get_lots_by_user(user_id: int, filters: dict | None = None) -> list[Lot]:
    session: Session = db()
    filters = filters or {}

    conditions = [Lot.user_id == user_id]

    # --------------------
    # Filtres métier
    # --------------------
    if filters.get("date_min"):
        conditions.append(Lot.date_achat >= filters["date_min"])

    if filters.get("date_max"):
        conditions.append(Lot.date_achat <= filters["date_max"])

    if filters.get("prix_min") is not None:
        conditions.append(Lot.prix_total_achat >= filters["prix_min"])

    if filters.get("prix_max") is not None:
        conditions.append(Lot.prix_total_achat <= filters["prix_max"])

    # --------------------
    # Pagination
    # --------------------
    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)

    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)

    offset = (page - 1) * page_size

    # --------------------
    # Tri sécurisé
    # --------------------
    order_by = (filters.get("order_by") or "id").lower()
    order_dir = (filters.get("order_dir") or "desc").lower()

    allowed_columns = {
        "id": Lot.id,
        "date_achat": Lot.date_achat,
        "prix_total_achat": Lot.prix_total_achat,
        "created_at": Lot.created_at,
        "updated_at": Lot.updated_at,
    }

    column = allowed_columns.get(order_by, Lot.id)

    order_expr = column.asc() if order_dir == "asc" else column.desc()

    stmt = (
        select(Lot)
        .where(and_(*conditions))
        .order_by(order_expr)
        .offset(offset)
        .limit(page_size)
    )

    return session.execute(stmt).scalars().all()


# =========================================================
# GET ONE (scopé par user)
# =========================================================

def get_lot_by_id_for_user(user_id: int, lot_id: int) -> Lot | None:
    session: Session = db()

    stmt = select(Lot).where(
        and_(Lot.id == lot_id, Lot.user_id == user_id)
    )

    return session.execute(stmt).scalars().first()


# =========================================================
# CREATE (user_id injecté depuis JWT)
# =========================================================

def create_lot_for_user(
    user_id: int,
    titre: str | None,
    description: str | None,
    prix_total_achat: float,
    date_achat=None,
) -> Lot:
    session: Session = db()

    item = Lot(
        user_id=user_id,
        titre=titre,
        description=description,
        prix_total_achat=prix_total_achat,
        date_achat=date_achat,
    )

    session.add(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# =========================================================
# PATCH (user scoped + sécurité totale)
# =========================================================

def patch_lot_for_user(
    user_id: int,
    lot_id: int,
    data: dict,
) -> Lot | None:
    session: Session = db()

    item = get_lot_by_id_for_user(user_id, lot_id)
    if item is None:
        return None

    # Interdire toute modification sensible
    data.pop("user_id", None)
    data.pop("id", None)
    data.pop("created_at", None)
    data.pop("updated_at", None)

    if "titre" in data:
        item.titre = data["titre"]

    if "description" in data:
        item.description = data["description"]

    if "prix_total_achat" in data:
        item.prix_total_achat = data["prix_total_achat"]

    if "date_achat" in data:
        item.date_achat = data["date_achat"]

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# =========================================================
# DELETE (user scoped)
# =========================================================

def delete_lot_for_user(user_id: int, lot_id: int) -> bool:
    session: Session = db()

    item = get_lot_by_id_for_user(user_id, lot_id)
    if item is None:
        return False

    session.delete(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True


# =========================================================
# COUNT (utile pour UI pagination)
# =========================================================

def count_lots_for_user(user_id: int) -> int:
    session: Session = db()

    stmt = select(func.count()).select_from(Lot).where(
        Lot.user_id == user_id
    )

    return int(session.execute(stmt).scalar_one())
