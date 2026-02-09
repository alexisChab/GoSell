from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.deps import db
from app.models.categorie import Category


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def get_categories(filters: dict | None = None):
    """
    Liste des catégories (optionnel: search/tri/pagination si tu veux).
    Pour l’instant minimal: retourne tout, tri par id.
    """
    session = db()

    stmt = select(Category).order_by(Category.id.asc())
    return session.execute(stmt).scalars().all()


def get_category_by_id(category_id: int) -> Category:
    session = db()

    stmt = select(Category).where(Category.id == category_id)
    obj = session.execute(stmt).scalars().first()
    if not obj:
        raise NotFoundError("Catégorie introuvable")
    return obj


def create_category(data: dict) -> Category:
    session = db()

    obj = Category(intitule=data["intitule"])
    session.add(obj)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("Une catégorie avec cet intitulé existe déjà")

    session.refresh(obj)
    return obj


def patch_category(category_id: int, patch: dict) -> Category:
    session = db()

    obj = session.execute(
        select(Category).where(Category.id == category_id)
    ).scalars().first()

    if not obj:
        raise NotFoundError("Catégorie introuvable")

    for field, value in patch.items():
        setattr(obj, field, value)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("Mise à jour impossible (intitulé déjà utilisé)")

    session.refresh(obj)
    return obj


def delete_category(category_id: int) -> None:
    session = db()

    obj = session.execute(
        select(Category).where(Category.id == category_id)
    ).scalars().first()

    if not obj:
        raise NotFoundError("Catégorie introuvable")

    session.delete(obj)
    session.commit()
