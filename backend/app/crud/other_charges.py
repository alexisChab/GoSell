from __future__ import annotations

from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.other_charges import OtherCharges
from app.models.lot import Lot




from app.models.product import Produit  # type: ignore
PRODUCT_MODEL = Produit


ALLOWED_ORDER_BY = {"id", "intitule", "montant", "lot_id", "produit_id"}


# =========================================================
# GET LIST (scopé user)
# =========================================================
def get_other_charges_by_user(user_id: int, filters: dict | None = None) -> list[OtherCharges]:
    session: Session = db()
    filters = filters or {}

    conditions = []

    # filtres
    if filters.get("lot_id") is not None:
        conditions.append(OtherCharges.lot_id == filters["lot_id"])
    if filters.get("produit_id") is not None:
        conditions.append(OtherCharges.produit_id == filters["produit_id"])

    # tri
    order_by = (filters.get("order_by") or "id").strip()
    if order_by not in ALLOWED_ORDER_BY:
        order_by = "id"
    order_dir = (filters.get("order_dir") or "desc").lower()
    col = getattr(OtherCharges, order_by, OtherCharges.id)
    col = col.asc() if order_dir == "asc" else col.desc()

    # pagination
    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size

    # sécurité user:
    # - soit charge rattachée à un lot (join Lot)
    # - soit rattachée à un produit (join Product/Produit)
    stmt = (
        select(OtherCharges)
        .outerjoin(Lot, Lot.id == OtherCharges.lot_id)
        .outerjoin(PRODUCT_MODEL, PRODUCT_MODEL.id == OtherCharges.produit_id)
        .where(
            and_(
                *conditions,
                or_(
                    and_(OtherCharges.lot_id.is_not(None), Lot.user_id == user_id),
                    and_(OtherCharges.produit_id.is_not(None), PRODUCT_MODEL.user_id == user_id),
                ),
            )
        )
        .order_by(col)
        .offset(offset)
        .limit(page_size)
    )

    return session.execute(stmt).scalars().all()


# =========================================================
# GET ONE (scopé user)
# =========================================================
def get_other_charge_by_id_for_user(user_id: int, charge_id: int) -> OtherCharges | None:
    session: Session = db()

    stmt = (
        select(OtherCharges)
        .outerjoin(Lot, Lot.id == OtherCharges.lot_id)
        .outerjoin(PRODUCT_MODEL, PRODUCT_MODEL.id == OtherCharges.produit_id)
        .where(
            and_(
                OtherCharges.id == charge_id,
                or_(
                    and_(OtherCharges.lot_id.is_not(None), Lot.user_id == user_id),
                    and_(OtherCharges.produit_id.is_not(None), PRODUCT_MODEL.user_id == user_id),
                ),
            )
        )
    )

    return session.execute(stmt).scalars().first()


# =========================================================
# CREATE (scopé user via lot/prod)
# =========================================================
def create_other_charge_for_user(
    user_id: int,
    intitule: str,
    montant: float,
    lot_id: int | None = None,
    produit_id: int | None = None,
) -> OtherCharges | None:
    session: Session = db()

    # XOR obligatoire
    if (lot_id is None and produit_id is None) or (lot_id is not None and produit_id is not None):
        raise ValueError("Exactly one of lot_id or produit_id must be provided.")

    # ownership check
    if lot_id is not None:
        ok = session.execute(select(Lot.id).where(and_(Lot.id == lot_id, Lot.user_id == user_id))).scalar_one_or_none()
        if ok is None:
            return None

    if produit_id is not None:
        ok = session.execute(
            select(PRODUCT_MODEL.id).where(and_(PRODUCT_MODEL.id == produit_id, PRODUCT_MODEL.user_id == user_id))
        ).scalar_one_or_none()
        if ok is None:
            return None

    item = OtherCharges(
        intitule=intitule,
        montant=montant,
        lot_id=lot_id,
        produit_id=produit_id,
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
# PATCH (scopé user)
# =========================================================
def patch_other_charge_for_user(
    user_id: int,
    charge_id: int,
    data: dict,
) -> OtherCharges | None:
    session: Session = db()

    item = get_other_charge_by_id_for_user(user_id, charge_id)
    if item is None:
        return None

    # interdit
    data.pop("id", None)

    # on patch les champs simples
    if "intitule" in data:
        item.intitule = data["intitule"]
    if "montant" in data:
        item.montant = data["montant"]

    # gestion lot_id / produit_id :
    # si tu veux AUTORISER de changer la cible, il faut appliquer la règle XOR
    if "lot_id" in data or "produit_id" in data:
        new_lot_id = data.get("lot_id", item.lot_id)
        new_produit_id = data.get("produit_id", item.produit_id)

        if (new_lot_id is None and new_produit_id is None) or (new_lot_id is not None and new_produit_id is not None):
            raise ValueError("Exactly one of lot_id or produit_id must be provided.")

        # ownership checks
        if new_lot_id is not None:
            ok = session.execute(
                select(Lot.id).where(and_(Lot.id == new_lot_id, Lot.user_id == user_id))
            ).scalar_one_or_none()
            if ok is None:
                return None

        if new_produit_id is not None:
            ok = session.execute(
                select(PRODUCT_MODEL.id).where(and_(PRODUCT_MODEL.id == new_produit_id, PRODUCT_MODEL.user_id == user_id))
            ).scalar_one_or_none()
            if ok is None:
                return None

        item.lot_id = new_lot_id
        item.produit_id = new_produit_id

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# =========================================================
# DELETE (scopé user)
# =========================================================
def delete_other_charge_for_user(user_id: int, charge_id: int) -> bool:
    session: Session = db()

    item = get_other_charge_by_id_for_user(user_id, charge_id)
    if item is None:
        return False

    session.delete(item)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True
