from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.db.deps import db
from app.models.delivery_charges import DeliveryCharges

def get_delivery_charges(filters: dict) -> list[DeliveryCharges]:
    session: Session = db()

    stmt = select(DeliveryCharges)

    if filters.get("produit_id"):
        stmt = stmt.where(DeliveryCharges.produit_id == filters["produit_id"])

    if filters.get("lot_id"):
        stmt = stmt.where(DeliveryCharges.lot_id == filters["lot_id"])

    if filters.get("societe_id"):
        stmt = stmt.where(DeliveryCharges.societe_id == filters["societe_id"])

    # ORDER
    order_by = filters.get("order_by", "id")
    order_dir = filters.get("order_dir", "desc")

    column = getattr(DeliveryCharges, order_by, DeliveryCharges.id)

    if order_dir == "asc":
        stmt = stmt.order_by(column.asc())
    else:
        stmt = stmt.order_by(column.desc())

    # PAGINATION
    page = int(filters.get("page", 1))
    page_size = int(filters.get("page_size", 20))

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    return session.execute(stmt).scalars().all()


def get_delivery_charge_by_id(charge_id: int) -> DeliveryCharges | None:
    session: Session = db()
    return session.get(DeliveryCharges, charge_id)


def create_delivery_charge(
    montant: float,
    produit_id: int,
    lot_id: int | None = None,
    societe_id: int | None = None,
) -> DeliveryCharges:

    session: Session = db()

    item = DeliveryCharges(
        montant=montant,
        produit_id=produit_id,
        lot_id=lot_id,
        societe_id=societe_id,
    )

    session.add(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


def patch_delivery_charge(
    charge_id: int,
    data: dict,
) -> DeliveryCharges | None:

    session: Session = db()

    item = session.get(DeliveryCharges, charge_id)
    if item is None:
        return None

    if "montant" in data:
        item.montant = data["montant"]

    if "produit_id" in data:
        item.produit_id = data["produit_id"]

    if "lot_id" in data:
        item.lot_id = data["lot_id"]

    if "societe_id" in data:
        item.societe_id = data["societe_id"]

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


def delete_delivery_charge(charge_id: int) -> bool:
    session: Session = db()

    item = session.get(DeliveryCharges, charge_id)
    if item is None:
        return False

    session.delete(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True
