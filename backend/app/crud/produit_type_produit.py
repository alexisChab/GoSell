from __future__ import annotations

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.produit_type_produit import ProduitTypeProduit


# ---------- GET LIST (filtres / pagination) ----------

def get_produit_type_produits(filters: dict) -> list[ProduitTypeProduit]:
    session: Session = db()

    conditions = []

    if filters.get("produit_id") is not None:
        conditions.append(ProduitTypeProduit.produit_id == filters["produit_id"])

    if filters.get("type_produit_id") is not None:
        conditions.append(ProduitTypeProduit.type_produit_id == filters["type_produit_id"])

    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    offset = (page - 1) * page_size

    stmt = select(ProduitTypeProduit).offset(offset).limit(page_size)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    return session.execute(stmt).scalars().all()


# ---------- GET BY (produit_id, type_produit_id) ----------

def get_produit_type_produit(produit_id: int, type_produit_id: int) -> ProduitTypeProduit | None:
    session: Session = db()
    # PK composite => get par tuple
    return session.get(ProduitTypeProduit, (produit_id, type_produit_id))


# ---------- CREATE (create link) ----------

def create_produit_type_produit(produit_id: int, type_produit_id: int) -> ProduitTypeProduit:
    session: Session = db()

    link = ProduitTypeProduit(produit_id=produit_id, type_produit_id=type_produit_id)
    session.add(link)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # - doublon (PK composite déjà existante)
        # - FK produit_id invalide
        # - FK type_produit_id invalide
        raise

    # refresh pas obligatoire sur table pivot, mais ok
    session.refresh(link)
    return link


# ---------- DELETE (delete link) ----------

def delete_produit_type_produit(produit_id: int, type_produit_id: int) -> bool:
    session: Session = db()

    link: ProduitTypeProduit | None = session.get(ProduitTypeProduit, (produit_id, type_produit_id))
    if link is None:
        return False

    session.delete(link)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True
