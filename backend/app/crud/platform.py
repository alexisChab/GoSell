# app/crud/platform.py
from __future__ import annotations

from sqlalchemy import select, and_
from app.db.deps import db
from app.models.platform import Platform
from sqlalchemy.exc import IntegrityError

class NotFoundError(Exception):
    pass


def get_platforms(filters: dict):
    """
    Retourne la liste des plateformes, avec filtres/pagination/tri.
    """
    session = db()

    conditions = []

    # search sur nom
    if filters.get("search"):
        conditions.append(Platform.nom.ilike(f"%{filters['search']}%"))

    # ranges
    if filters.get("frais_supp_eur_min") is not None:
        conditions.append(Platform.frais_supp_eur >= filters["frais_supp_eur_min"])
    if filters.get("frais_supp_eur_max") is not None:
        conditions.append(Platform.frais_supp_eur <= filters["frais_supp_eur_max"])

    if filters.get("pourcentage_vente_min") is not None:
        conditions.append(Platform.pourcentage_vente >= filters["pourcentage_vente_min"])
    if filters.get("pourcentage_vente_max") is not None:
        conditions.append(Platform.pourcentage_vente <= filters["pourcentage_vente_max"])

    # order by
    order_by = filters.get("order_by") or "id"
    order_dir = filters.get("order_dir", "asc")
    col = getattr(Platform, order_by, Platform.id)
    col = col.desc() if order_dir == "desc" else col.asc()

    # pagination
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 20)
    offset = (page - 1) * page_size

    stmt = select(Platform)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(col).offset(offset).limit(page_size)

    return session.execute(stmt).scalars().all()


def get_platform_by_id(platform_id: int) -> Platform:
    """
    Retourne une plateforme par id.
    """
    session = db()
    stmt = select(Platform).where(Platform.id == platform_id)
    obj = session.execute(stmt).scalars().first()
    if not obj:
        raise NotFoundError("Plateforme introuvable")
    return obj

class ConflictError(Exception):
    pass


def create_platform(data: dict) -> Platform:
    """
    Crée une plateforme.
    data vient de PlatformCreateSchema.load(...)
    """
    session = db()

    # Optionnel: empêcher doublons de nom (si tu veux).
    # Si tu n'as pas de contrainte unique en DB, ce check aide quand même.
    existing = session.execute(select(Platform).where(Platform.nom == data["nom"])).scalars().first()
    if existing:
        raise ConflictError("Une plateforme avec ce nom existe déjà")

    platform = Platform(
        nom=data["nom"],
        frais_supp_eur=data.get("frais_supp_eur", 0),
        pourcentage_vente=data.get("pourcentage_vente", 0),
        lien_homepage=data.get("lien_homepage"),
    )

    session.add(platform)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # au cas où tu ajoutes une contrainte unique plus tard
        raise ConflictError("Création impossible (conflit/contrainte)")
    session.refresh(platform)
    return platform


def delete_platform(platform_id: int) -> None:
    """
    Supprime une plateforme par id.
    Le modèle a une relation ou_vente avec cascade="all, delete-orphan".
    Si tu utilises delete() direct, ça peut bypass certains cascades ORM.
    Donc ici on charge l'objet et on session.delete(obj) pour respecter l'ORM.
    """
    session = db()

    platform = session.execute(select(Platform).where(Platform.id == platform_id)).scalars().first()
    if not platform:
        raise NotFoundError("Plateforme introuvable")

    session.delete(platform)
    session.commit()

def patch_platform(platform_id: int, patch: dict) -> Platform:
    """
    Update partiel d'une plateforme.
    patch vient de PlatformPatchSchema.load(..., partial=True)
    """
    session = db()

    platform = session.execute(
        select(Platform).where(Platform.id == platform_id)
    ).scalars().first()

    if not platform:
        raise NotFoundError("Plateforme introuvable")

    if "nom" in patch and patch["nom"] is not None:
        existing = session.execute(
            select(Platform).where(Platform.nom == patch["nom"], Platform.id != platform_id)
        ).scalars().first()
        if existing:
            raise ConflictError("Une plateforme avec ce nom existe déjà")

    for field, value in patch.items():
        setattr(platform, field, value)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ConflictError("Mise à jour impossible (conflit/contrainte)")

    session.refresh(platform)
    return platform