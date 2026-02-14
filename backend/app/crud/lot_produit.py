from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.lot_produit import LotProduit
from app.models.lot import Lot


# ---------- GET LIST (scopé user via Lot.user_id) ----------

ALLOWED_ORDER_BY = {"id", "lot_id", "produit_id", "quantite", "allocation_prix_achat", "allocation_frais", "allocation_methode"}


def get_lot_produits_by_user(user_id: int, filters: dict) -> list[LotProduit]:
    session: Session = db()

    conditions = [Lot.user_id == user_id]

    # filtres
    if filters.get("lot_id") is not None:
        conditions.append(LotProduit.lot_id == filters["lot_id"])
    if filters.get("produit_id") is not None:
        conditions.append(LotProduit.produit_id == filters["produit_id"])

    # tri (sécurisé)
    order_by = (filters.get("order_by") or "id").strip()
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "id"

    order_dir = (filters.get("order_dir") or "desc").lower()
    col = getattr(LotProduit, order_by, LotProduit.id)
    col = col.desc() if order_dir == "desc" else col.asc()

    # pagination
    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size

    stmt = (
        select(LotProduit)
        .join(Lot, Lot.id == LotProduit.lot_id)
        .where(and_(*conditions))
        .order_by(col)
        .offset(offset)
        .limit(page_size)
    )

    return session.execute(stmt).scalars().all()


# ---------- GET BY ID (scopé user via Lot.user_id) ----------

def get_lot_produit_by_id_for_user(user_id: int, lot_produit_id: int) -> LotProduit | None:
    session: Session = db()

    stmt = (
        select(LotProduit)
        .join(Lot, Lot.id == LotProduit.lot_id)
        .where(and_(LotProduit.id == lot_produit_id, Lot.user_id == user_id))
    )
    return session.execute(stmt).scalars().first()


# ---------- CREATE (scopé user via lot_id) ----------

def create_lot_produit_for_user(
    user_id: int,
    lot_id: int,
    produit_id: int,
    quantite: int = 1,
    allocation_prix_achat: float | None = None,
    allocation_frais: float | None = None,
    allocation_methode: str | None = None,
) -> LotProduit | None:
    session: Session = db()

    # sécurité : le lot doit appartenir au user
    lot_ok = session.execute(
        select(Lot.id).where(and_(Lot.id == lot_id, Lot.user_id == user_id))
    ).scalar_one_or_none()
    if lot_ok is None:
        return None

    item = LotProduit(
        lot_id=lot_id,
        produit_id=produit_id,
        quantite=quantite,
        allocation_prix_achat=allocation_prix_achat,
        allocation_frais=allocation_frais,
        allocation_methode=allocation_methode,
    )

    session.add(item)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# ---------- PATCH (scopé user) ----------

def patch_lot_produit_for_user(
    user_id: int,
    lot_produit_id: int,
    data: dict,
) -> LotProduit | None:
    session: Session = db()

    item = get_lot_produit_by_id_for_user(user_id, lot_produit_id)
    if item is None:
        return None

    # interdit de patch les FK / id
    data.pop("id", None)
    data.pop("lot_id", None)
    data.pop("produit_id", None)

    if "quantite" in data:
        item.quantite = data["quantite"]
    if "allocation_prix_achat" in data:
        item.allocation_prix_achat = data["allocation_prix_achat"]
    if "allocation_frais" in data:
        item.allocation_frais = data["allocation_frais"]
    if "allocation_methode" in data:
        item.allocation_methode = data["allocation_methode"]

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# ---------- DELETE (scopé user) ----------

def delete_lot_produit_for_user(user_id: int, lot_produit_id: int) -> bool:
    session: Session = db()

    item = get_lot_produit_by_id_for_user(user_id, lot_produit_id)
    if item is None:
        return False

    session.delete(item)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True
