from __future__ import annotations

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.db.deps import db

from app.models.product import Produit
from app.models.lot import Lot
from app.models.stock import Stock

from app.crud.benefice import (
    get_benefice_summary_for_user,
    get_risk_products_for_user,
    get_best_types_for_user,
)


def get_dashboard_summary_for_user(user_id: int) -> dict:
    session: Session = db()

    # -------- counts produits --------
    nb_produits_total = session.execute(
        select(func.count(Produit.id)).where(Produit.user_id == user_id)
    ).scalar_one()

    nb_produits_en_vente = session.execute(
        select(func.count(Produit.id)).where(and_(Produit.user_id == user_id, Produit.en_vente == True))  # noqa: E712
    ).scalar_one()

    nb_produits_vendus = session.execute(
        select(func.count(Produit.id)).where(and_(Produit.user_id == user_id, Produit.est_vendu == True))  # noqa: E712
    ).scalar_one()

    # -------- counts lots / stocks --------
    nb_lots = session.execute(
        select(func.count(Lot.id)).where(Lot.user_id == user_id)
    ).scalar_one()

    nb_stocks = session.execute(
        select(func.count(Stock.id)).where(Stock.user_id == user_id)
    ).scalar_one()

    counts = {
        "nb_produits_total": int(nb_produits_total or 0),
        "nb_produits_en_vente": int(nb_produits_en_vente or 0),
        "nb_produits_vendus": int(nb_produits_vendus or 0),
        "nb_lots": int(nb_lots or 0),
        "nb_stocks": int(nb_stocks or 0),
    }

    # -------- bénéfices global (déjà existant) --------
    benefices = get_benefice_summary_for_user(
        user_id=user_id,
        filters={
            "include_products": True,
            "include_stocks": True,
            "include_fees": True,
            # pas de filtre ici (dashboard = global)
        },
    )

    # -------- risk products (top 5) --------
    risk_products = get_risk_products_for_user(
        user_id=user_id,
        filters={
            "limit": 5,
            "only_en_vente": True,
            "include_lot_products": False,
            "threshold_multiple": 1.0,
        },
    )

    # -------- best types (top 5) --------
    best_types = get_best_types_for_user(
        user_id=user_id,
        filters={
            "min_multiple": 1.5,
            "min_count": 1,
            "only_en_vente": True,
            "exclude_lot_products": True,
            "max_avg_cost_total": None,
            "categorie_id": None,
            "genre_id": None,
            "limit": 5,
        },
    )

    return {
        "counts": counts,
        "benefices": benefices,
        "risk_products": risk_products,
        "best_types": best_types,
    }