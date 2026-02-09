from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from app.db.deps import db
from app.models.delivery_company import DeliveryCompany


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def get_delivery_companies(filters: dict):
    """
    Liste des sociétés de livraison avec filtres/pagination/tri.
    Filtres attendus (si tu as fait un FilterSchema) :
      - search
      - order_by (id|nom)
      - order_dir (asc|desc)
      - page
      - page_size
    """
    session = db()

    conditions = []

    if filters.get("search"):
        conditions.append(DeliveryCompany.nom.ilike(f"%{filters['search']}%"))

    order_by = filters.get("order_by") or "id"
    order_dir = filters.get("order_dir", "asc")

    col = getattr(DeliveryCompany, order_by, DeliveryCompany.id)
    col = col.desc() if order_dir == "desc" else col.asc()

    page = filters.get("page", 1)
    page_size = filters.get("page_size", 20)
    offset = (page - 1) * page_size

    stmt = select(DeliveryCompany)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(col).offset(offset).limit(page_size)

    return session.execute(stmt).scalars().all()


def get_delivery_company_by_id(company_id: int) -> DeliveryCompany:
    session = db()
    stmt = select(DeliveryCompany).where(DeliveryCompany.id == company_id)
    obj = session.execute(stmt).scalars().first()
    if not obj:
        raise NotFoundError("Société de livraison introuvable")
    return obj


def create_delivery_company(data: dict) -> DeliveryCompany:
    """
    Create. data vient de DeliveryCompanyCreateSchema.load(...)
    """
    session = db()

    obj = DeliveryCompany(
        nom=data["nom"],
    )

    session.add(obj)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # nom est unique=True -> conflit si déjà existant
        raise ConflictError("Une société de livraison avec ce nom existe déjà")

    session.refresh(obj)
    return obj


def patch_delivery_company(company_id: int, patch: dict) -> DeliveryCompany:
    """
    Patch partiel. patch vient de DeliveryCompanyPatchSchema.load(..., partial=True)
    """
    session = db()

    obj = session.execute(
        select(DeliveryCompany).where(DeliveryCompany.id == company_id)
    ).scalars().first()

    if not obj:
        raise NotFoundError("Société de livraison introuvable")

    for field, value in patch.items():
        setattr(obj, field, value)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("Mise à jour impossible (nom déjà utilisé)")

    session.refresh(obj)
    return obj


def delete_delivery_company(company_id: int) -> None:
    """
    Delete via ORM pour respecter cascade frais_livraison.
    """
    session = db()

    obj = session.execute(
        select(DeliveryCompany).where(DeliveryCompany.id == company_id)
    ).scalars().first()

    if not obj:
        raise NotFoundError("Société de livraison introuvable")

    session.delete(obj)
    session.commit()
