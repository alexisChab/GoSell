from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.where_sell import WhereSell


# -------------------------------------------------------
# GET LIST (avec filtres + pagination)
# -------------------------------------------------------

def get_where_sells(filters: dict) -> list[WhereSell]:
    session: Session = db()

    conditions = []

    if filters.get("produit_id") is not None:
        conditions.append(WhereSell.produit_id == filters["produit_id"])

    if filters.get("plateforme_id") is not None:
        conditions.append(WhereSell.plateforme_id == filters["plateforme_id"])

    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)

    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)

    offset = (page - 1) * page_size

    stmt = select(WhereSell).offset(offset).limit(page_size)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    return session.execute(stmt).scalars().all()


# -------------------------------------------------------
# GET ONE (PK composite)
# -------------------------------------------------------

def get_where_sell(produit_id: int, plateforme_id: int) -> WhereSell | None:
    session: Session = db()
    return session.get(WhereSell, (produit_id, plateforme_id))


# -------------------------------------------------------
# CREATE
# -------------------------------------------------------

def create_where_sell(
    produit_id: int,
    plateforme_id: int,
    lien: str | None = None,
) -> WhereSell:
    session: Session = db()

    item = WhereSell(
        produit_id=produit_id,
        plateforme_id=plateforme_id,
        lien=lien,
    )

    session.add(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # FK invalide ou doublon PK composite
        raise

    session.refresh(item)
    return item


# -------------------------------------------------------
# PATCH (uniquement lien)
# -------------------------------------------------------

def patch_where_sell(
    produit_id: int,
    plateforme_id: int,
    data: dict,
) -> WhereSell | None:
    session: Session = db()

    item: WhereSell | None = session.get(
        WhereSell, (produit_id, plateforme_id)
    )
    if item is None:
        return None

    if "lien" in data:
        item.lien = data["lien"]

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# -------------------------------------------------------
# DELETE
# -------------------------------------------------------

def delete_where_sell(
    produit_id: int,
    plateforme_id: int,
) -> bool:
    session: Session = db()

    item: WhereSell | None = session.get(
        WhereSell, (produit_id, plateforme_id)
    )
    if item is None:
        return False

    session.delete(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True

