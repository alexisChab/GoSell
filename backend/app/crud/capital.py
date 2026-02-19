from __future__ import annotations

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.product import Produit
from app.models.lot import Lot
from app.models.stock import Stock
from app.models.lot_produit import LotProduit

from app.models.produit_type_produit import ProduitTypeProduit
from app.models.product_type import ProductType
from app.models.genre import Genre
from app.models.categorie import Category


def get_capital_for_user(user_id: int, filters: dict) -> dict:
    session: Session = db()

    include_products = bool(filters.get("include_products", True))
    include_lots = bool(filters.get("include_lots", True))
    include_stocks = bool(filters.get("include_stocks", True))

    only_unsold_products = bool(filters.get("only_unsold_products", True))
    exclude_lot_products = bool(filters.get("exclude_lot_products", True))

    categorie_id = filters.get("categorie_id")
    genre_id = filters.get("genre_id")
    type_produit_id = filters.get("type_produit_id")
    need_taxonomy_join = any(x is not None for x in (categorie_id, genre_id, type_produit_id))

    # -------------------------
    # PRODUCTS capital
    # -------------------------
    capital_products = 0.0
    nb_products = 0

    if include_products:
        conds = [
            Produit.user_id == user_id,
            Produit.a_ete_achete == True,  # noqa: E712
            Produit.prix_achat.isnot(None),
        ]
        if only_unsold_products:
            conds.append(Produit.est_vendu == False)  # noqa: E712

        stmt = select(
            func.coalesce(func.sum(Produit.prix_achat), 0.0).label("sum_achat"),
            func.count(func.distinct(Produit.id)).label("nb"),
        ).where(and_(*conds))

        if need_taxonomy_join:
            stmt = (
                stmt.join(ProduitTypeProduit, ProduitTypeProduit.produit_id == Produit.id)
                    .join(ProductType, ProductType.id == ProduitTypeProduit.type_produit_id)
                    .join(Genre, Genre.id == ProductType.genre_id)
                    .join(Category, Category.id == Genre.categorie_id)
            )
            if type_produit_id is not None:
                stmt = stmt.where(ProductType.id == int(type_produit_id))
            if genre_id is not None:
                stmt = stmt.where(Genre.id == int(genre_id))
            if categorie_id is not None:
                stmt = stmt.where(Category.id == int(categorie_id))

        if exclude_lot_products:
            stmt = stmt.where(
                ~select(LotProduit.id).where(LotProduit.produit_id == Produit.id).exists()
            )

        row = session.execute(stmt).first()
        if row:
            capital_products = float(row.sum_achat or 0.0)
            nb_products = int(row.nb or 0)

    # -------------------------
    # LOTS capital (prix_total_achat)
    # -------------------------
    capital_lots = 0.0
    nb_lots = 0

    if include_lots:
        stmt_lots = select(
            func.coalesce(func.sum(Lot.prix_total_achat), 0.0).label("sum_lots"),
            func.count(Lot.id).label("nb"),
        ).where(
            and_(
                Lot.user_id == user_id,
                Lot.prix_total_achat.isnot(None),
            )
        )

        row_l = session.execute(stmt_lots).first()
        if row_l:
            capital_lots = float(row_l.sum_lots or 0.0)
            nb_lots = int(row_l.nb or 0)

    # -------------------------
    # STOCKS capital
    # -------------------------
    capital_stocks = 0.0
    nb_stocks = 0

    if include_stocks:
        stmt_s = select(
            func.coalesce(func.sum(Stock.prix_achat), 0.0).label("sum_stocks"),
            func.count(Stock.id).label("nb"),
        ).where(
            and_(
                Stock.user_id == user_id,
                Stock.a_ete_achete == True,  # noqa: E712
                Stock.prix_achat.isnot(None),
            )
        )

        row_s = session.execute(stmt_s).first()
        if row_s:
            capital_stocks = float(row_s.sum_stocks or 0.0)
            nb_stocks = int(row_s.nb or 0)

    capital_total = float(capital_products) + float(capital_lots) + float(capital_stocks)

    return {
        "scope": {
            "include_products": include_products,
            "include_lots": include_lots,
            "include_stocks": include_stocks,
            "only_unsold_products": only_unsold_products,
            "exclude_lot_products": exclude_lot_products,
            "categorie_id": categorie_id,
            "genre_id": genre_id,
            "type_produit_id": type_produit_id,
        },
        "counts": {
            "nb_products_counted": nb_products,
            "nb_lots_counted": nb_lots,
            "nb_stocks_counted": nb_stocks,
        },
        "totals": {
            "capital_products": float(capital_products),
            "capital_lots": float(capital_lots),
            "capital_stocks": float(capital_stocks),
            "capital_total": float(capital_total),
        },
    }