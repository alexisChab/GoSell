from __future__ import annotations

from sqlalchemy import select, and_, func, case, literal, cast, Float
from sqlalchemy.orm import Session

from app.db.deps import db

from app.models.product import Produit
from app.models.stock import Stock

from app.models.produit_type_produit import ProduitTypeProduit
from app.models.product_type import ProductType
from app.models.genre import Genre
from app.models.categorie import Category

from app.models.lot_produit import LotProduit

from app.models.delivery_charges import DeliveryCharges
from app.models.other_charges import OtherCharges


def _parse_ids_csv(value: str | None) -> list[int] | None:
    if not value:
        return None
    out: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out or None


def _median_expr(prix_min_col, prix_max_col):
    """
    médian espéré :
      - min+max -> (min+max)/2
      - min seul -> min
      - max seul -> max
      - sinon -> NULL
    """
    return case(
        (
            and_(prix_min_col.isnot(None), prix_max_col.isnot(None)),
            (cast(prix_min_col, Float) + cast(prix_max_col, Float)) / 2.0,
        ),
        (prix_min_col.isnot(None), cast(prix_min_col, Float)),
        (prix_max_col.isnot(None), cast(prix_max_col, Float)),
        else_=None,
    )


def get_benefice_summary_for_user(user_id: int, filters: dict) -> dict:
    """
    Résumé bénéfice global basé sur le prix médian espéré.
    - Produits: revenue attendu = somme(médian), cost = somme(prix_achat_effectif) (+ fees si include_fees)
    - Stocks: cost = somme(prix_achat_effectif)
    - profit = revenue_expected_median - cost_total
    """
    session: Session = db()

    include_products = bool(filters.get("include_products", True))
    include_stocks = bool(filters.get("include_stocks", True))
    include_fees = bool(filters.get("include_fees", True))

    # -------------------------
    # Produits: conditions
    # -------------------------
    prod_conditions = [Produit.user_id == user_id]

    for key, colname in [
        ("products_en_vente", "en_vente"),
        ("products_est_vendu", "est_vendu"),
        ("products_a_ete_achete", "a_ete_achete"),
    ]:
        if filters.get(key) is not None:
            prod_conditions.append(getattr(Produit, colname) == filters[key])

    if filters.get("products_prix_achat_min") is not None:
        prod_conditions.append(Produit.prix_achat >= filters["products_prix_achat_min"])
    if filters.get("products_prix_achat_max") is not None:
        prod_conditions.append(Produit.prix_achat <= filters["products_prix_achat_max"])

    product_ids = _parse_ids_csv(filters.get("product_ids"))
    if product_ids:
        prod_conditions.append(Produit.id.in_(product_ids))

    exclude_lot_products = bool(filters.get("exclude_lot_products", False))

    # taxonomie
    categorie_id = filters.get("categorie_id")
    genre_id = filters.get("genre_id")
    type_produit_id = filters.get("type_produit_id")

    need_taxonomy_join = any(x is not None for x in (type_produit_id, genre_id, categorie_id))

    # -------------------------
    # Stocks: conditions
    # -------------------------
    stock_conditions = [Stock.user_id == user_id]

    if filters.get("stocks_a_ete_achete") is not None:
        stock_conditions.append(Stock.a_ete_achete == filters["stocks_a_ete_achete"])

    if filters.get("stocks_prix_achat_min") is not None:
        stock_conditions.append(Stock.prix_achat >= filters["stocks_prix_achat_min"])
    if filters.get("stocks_prix_achat_max") is not None:
        stock_conditions.append(Stock.prix_achat <= filters["stocks_prix_achat_max"])

    stock_ids = _parse_ids_csv(filters.get("stock_ids"))
    if stock_ids:
        stock_conditions.append(Stock.id.in_(stock_ids))

    # -------------------------
    # Agrégats produits
    # -------------------------
    nb_produits = 0
    nb_missing_expected = 0
    nb_missing_cost = 0
    revenue_expected_median = 0.0
    cost_products = 0.0

    selected_product_ids: list[int] = []

    if include_products:
        median = _median_expr(Produit.prix_min_espere, Produit.prix_max_espere)

        # coût achat effectif:
        # gratuit => 0 ; acheté => prix_achat (peut être NULL)
        cost_eff = case(
            (Produit.a_ete_achete == False, literal(0.0)),  # noqa: E712
            else_=cast(Produit.prix_achat, Float),
        )

        stmt = select(
            func.count(func.distinct(Produit.id)).label("nb"),
            func.coalesce(func.sum(median), 0.0).label("sum_median"),
            func.coalesce(func.sum(cost_eff), 0.0).label("sum_cost"),
            func.coalesce(func.sum(case((median.is_(None), 1), else_=0)), 0).label("missing_expected"),
            func.coalesce(
                func.sum(
                    case(
                        (and_(Produit.a_ete_achete == True, Produit.prix_achat.is_(None)), 1),  # noqa: E712
                        else_=0,
                    )
                ),
                0,
            ).label("missing_cost"),
        ).where(and_(*prod_conditions))

        if need_taxonomy_join:
            stmt = (
                stmt.join(ProduitTypeProduit, ProduitTypeProduit.produit_id == Produit.id)
                    .join(ProductType, ProductType.id == ProduitTypeProduit.type_produit_id)
                    .join(Genre, Genre.id == ProductType.genre_id)
                    .join(Category, Category.id == Genre.categorie_id)
            )
            if type_produit_id is not None:
                stmt = stmt.where(ProductType.id == type_produit_id)
            if genre_id is not None:
                stmt = stmt.where(Genre.id == genre_id)
            if categorie_id is not None:
                stmt = stmt.where(Category.id == categorie_id)

        if exclude_lot_products:
            stmt = stmt.where(
                ~select(LotProduit.id).where(LotProduit.produit_id == Produit.id).exists()
            )

        row = session.execute(stmt).first()
        if row:
            nb_produits = int(row.nb or 0)
            revenue_expected_median = float(row.sum_median or 0.0)
            cost_products = float(row.sum_cost or 0.0)
            nb_missing_expected = int(row.missing_expected or 0)
            nb_missing_cost = int(row.missing_cost or 0)

        # IDs produits sélectionnés (pour fees)
        if include_fees and nb_produits > 0:
            id_stmt = select(func.distinct(Produit.id)).where(and_(*prod_conditions))
            if need_taxonomy_join:
                id_stmt = (
                    id_stmt.join(ProduitTypeProduit, ProduitTypeProduit.produit_id == Produit.id)
                          .join(ProductType, ProductType.id == ProduitTypeProduit.type_produit_id)
                          .join(Genre, Genre.id == ProductType.genre_id)
                          .join(Category, Category.id == Genre.categorie_id)
                )
                if type_produit_id is not None:
                    id_stmt = id_stmt.where(ProductType.id == type_produit_id)
                if genre_id is not None:
                    id_stmt = id_stmt.where(Genre.id == genre_id)
                if categorie_id is not None:
                    id_stmt = id_stmt.where(Category.id == categorie_id)

            if exclude_lot_products:
                id_stmt = id_stmt.where(
                    ~select(LotProduit.id).where(LotProduit.produit_id == Produit.id).exists()
                )

            selected_product_ids = [r[0] for r in session.execute(id_stmt).all()]

    # -------------------------
    # Agrégats stocks
    # -------------------------
    nb_stocks = 0
    cost_stocks = 0.0

    if include_stocks:
        stock_cost_eff = case(
            (Stock.a_ete_achete == False, literal(0.0)),  # noqa: E712
            else_=cast(Stock.prix_achat, Float),
        )

        stmt_s = select(
            func.count(Stock.id).label("nb"),
            func.coalesce(func.sum(stock_cost_eff), 0.0).label("sum_cost"),
        ).where(and_(*stock_conditions))

        row_s = session.execute(stmt_s).first()
        if row_s:
            nb_stocks = int(row_s.nb or 0)
            cost_stocks = float(row_s.sum_cost or 0.0)

    # -------------------------
    # Fees produits
    # -------------------------
    fees = 0.0
    if include_fees and selected_product_ids:
        fees_delivery = session.execute(
            select(func.coalesce(func.sum(DeliveryCharges.montant), 0.0))
            .where(DeliveryCharges.produit_id.in_(selected_product_ids))
        ).scalar_one()

        fees_other = session.execute(
            select(func.coalesce(func.sum(OtherCharges.montant), 0.0))
            .where(OtherCharges.produit_id.in_(selected_product_ids))
        ).scalar_one()

        fees = float(fees_delivery or 0.0) + float(fees_other or 0.0)

    # -------------------------
    # Totaux
    # -------------------------
    cost_total = float(cost_products) + float(cost_stocks) + float(fees)
    profit_expected_median = float(revenue_expected_median) - float(cost_total)

    return {
        "scope": {
            "include_products": include_products,
            "include_stocks": include_stocks,
            "include_fees": include_fees,
        },
        "counts": {
            "nb_produits": nb_produits,
            "nb_stocks": nb_stocks,
            "nb_produits_ignored_missing_expected": nb_missing_expected,
            "nb_produits_ignored_missing_cost": nb_missing_cost,
        },
        "totals": {
            "cost_products": float(cost_products),
            "cost_stocks": float(cost_stocks),
            "fees": float(fees),
            "cost_total": float(cost_total),
            "revenue_expected_median": float(revenue_expected_median),
            "profit_expected_median": float(profit_expected_median),
            "is_profit_expected_median": profit_expected_median > 0,
        },
    }
def _median_expected(pmin, pmax) -> float | None:
    if pmin is None and pmax is None:
        return None
    if pmin is None:
        return float(pmax)
    if pmax is None:
        return float(pmin)
    return (float(pmin) + float(pmax)) / 2.0


def _apply_haircut(price: float | None, haircut_percent: float | None) -> float | None:
    if price is None:
        return None
    if haircut_percent is None:
        return float(price)
    return float(price) * (1.0 - float(haircut_percent) / 100.0)


def _kpi(price: float | None, cost_total: float | None) -> dict:
    """
    Renvoie un dict compatible ProfitKpiSchema.
    """
    if price is None or cost_total is None:
        return {
            "price": None if price is None else float(price),
            "cost_total": None if cost_total is None else float(cost_total),
            "profit_amount": None,
            "multiple": None,
            "is_profit": None,
        }

    price = float(price)
    cost_total = float(cost_total)
    profit_amount = price - cost_total

    if cost_total == 0:
        # multiple indéfini/infini
        multiple = None
    else:
        multiple = price / cost_total

    return {
        "price": price,
        "cost_total": cost_total,
        "profit_amount": float(profit_amount),
        "multiple": None if multiple is None else float(multiple),
        "is_profit": profit_amount > 0,
    }


def _get_product_cost_context_for_user(session: Session, user_id: int, product_id: int) -> dict | None:
    """
    Contexte commun :
    - anti-leak
    - from_lot
    - a_ete_achete
    - pmin/pmax/pmed
    - cost_total (si calculable)
    - reason si pas calculable
    """
    stmt = select(Produit).where(and_(Produit.id == product_id, Produit.user_id == user_id))
    produit = session.execute(stmt).scalars().first()
    if not produit:
        return None

    # from_lot ?
    from_lot = (
        session.execute(
            select(LotProduit.id).where(LotProduit.produit_id == product_id).limit(1)
        ).first()
        is not None
    )

    pmin = produit.prix_min_espere
    pmax = produit.prix_max_espere
    pmed = _median_expected(pmin, pmax)

    # frais produit
    delivery_sum = session.execute(
        select(func.coalesce(func.sum(DeliveryCharges.montant), 0.0))
        .where(DeliveryCharges.produit_id == product_id)
    ).scalar_one()
    other_sum = session.execute(
        select(func.coalesce(func.sum(OtherCharges.montant), 0.0))
        .where(OtherCharges.produit_id == product_id)
    ).scalar_one()

    fees_total = float(delivery_sum or 0.0) + float(other_sum or 0.0)

    # règle lot : stop
    if from_lot:
        return {
            "produit": produit,
            "from_lot": True,
            "reason": "CALCUL_AU_NIVEAU_DU_LOT",
            "pmin": None if pmin is None else float(pmin),
            "pmax": None if pmax is None else float(pmax),
            "pmed": None if pmed is None else float(pmed),
            "fees_total": fees_total,
            "cost_total": None,
        }

    # coût achat
    if not produit.a_ete_achete:
        cout_achat = 0.0
    else:
        if produit.prix_achat is None:
            return {
                "produit": produit,
                "from_lot": False,
                "reason": "PRIX_ACHAT_MANQUANT",
                "pmin": None if pmin is None else float(pmin),
                "pmax": None if pmax is None else float(pmax),
                "pmed": None if pmed is None else float(pmed),
                "fees_total": fees_total,
                "cost_total": None,
            }
        cout_achat = float(produit.prix_achat)

    cost_total = float(cout_achat) + float(fees_total)

    return {
        "produit": produit,
        "from_lot": False,
        "reason": None,
        "pmin": None if pmin is None else float(pmin),
        "pmax": None if pmax is None else float(pmax),
        "pmed": None if pmed is None else float(pmed),
        "fees_total": fees_total,
        "cost_total": cost_total,
    }


def get_product_whatif_for_user(user_id: int, product_id: int, offer_price: float) -> dict | None:
    """
    GET /products/<id>/whatif?offer_price=...
    """
    session: Session = db()
    ctx = _get_product_cost_context_for_user(session, user_id, product_id)
    if ctx is None:
        return None

    produit = ctx["produit"]
    from_lot = bool(ctx["from_lot"])
    reason = ctx["reason"]

    # si lot => pas de calcul
    if from_lot:
        return {
            "product_id": produit.id,
            "from_lot": True,
            "a_ete_achete": bool(produit.a_ete_achete),
            "offer": _kpi(float(offer_price), None),
            "reason": reason,
        }

    cost_total = ctx["cost_total"]
    if cost_total is None:
        # ex: PRIX_ACHAT_MANQUANT
        return {
            "product_id": produit.id,
            "from_lot": False,
            "a_ete_achete": bool(produit.a_ete_achete),
            "offer": _kpi(float(offer_price), None),
            "reason": reason,
        }

    kpi = _kpi(float(offer_price), float(cost_total))

    # si coût total == 0 -> multiple None, on remonte le reason
    out_reason = None
    if float(cost_total) == 0:
        out_reason = "ZERO_COST"

    return {
        "product_id": produit.id,
        "from_lot": False,
        "a_ete_achete": bool(produit.a_ete_achete),
        "offer": kpi,
        "reason": out_reason,
    }


def get_product_forecast_for_user(
    user_id: int,
    product_id: int,
    offer_price: float | None = None,
    haircut_percent: float | None = None,
) -> dict | None:
    """
    GET /products/<id>/forecast
    GET /products/<id>/forecast?offer_price=...
    GET /products/<id>/forecast?haircut_percent=...
    """
    session: Session = db()
    ctx = _get_product_cost_context_for_user(session, user_id, product_id)
    if ctx is None:
        return None

    produit = ctx["produit"]
    from_lot = bool(ctx["from_lot"])
    reason = ctx["reason"]

    # lot => stop
    if from_lot:
        return {
            "product_id": produit.id,
            "from_lot": True,
            "a_ete_achete": bool(produit.a_ete_achete),
            "haircut_percent": haircut_percent,
            "cost_total": None,
            "scenarios": {
                "min": _kpi(None, None),
                "median": _kpi(None, None),
                "max": _kpi(None, None),
                "offer": None,
            },
            "reason": reason,
        }

    cost_total = ctx["cost_total"]
    if cost_total is None:
        # PRIX_ACHAT_MANQUANT
        return {
            "product_id": produit.id,
            "from_lot": False,
            "a_ete_achete": bool(produit.a_ete_achete),
            "haircut_percent": haircut_percent,
            "cost_total": None,
            "scenarios": {
                "min": _kpi(None, None),
                "median": _kpi(None, None),
                "max": _kpi(None, None),
                "offer": None,
            },
            "reason": reason,
        }

    pmin = _apply_haircut(ctx["pmin"], haircut_percent)
    pmed = _apply_haircut(ctx["pmed"], haircut_percent)
    pmax = _apply_haircut(ctx["pmax"], haircut_percent)

    # si on n'a aucun prix espéré, on renvoie insuffisant
    if pmin is None and pmed is None and pmax is None:
        return {
            "product_id": produit.id,
            "from_lot": False,
            "a_ete_achete": bool(produit.a_ete_achete),
            "haircut_percent": haircut_percent,
            "cost_total": float(cost_total),
            "scenarios": {
                "min": _kpi(None, float(cost_total)),
                "median": _kpi(None, float(cost_total)),
                "max": _kpi(None, float(cost_total)),
                "offer": None,
            },
            "reason": "PRIX_ESPERES_INSUFFISANTS",
        }

    scenarios = {
        "min": _kpi(pmin, float(cost_total)),
        "median": _kpi(pmed, float(cost_total)),
        "max": _kpi(pmax, float(cost_total)),
        "offer": None,
    }

    if offer_price is not None:
        scenarios["offer"] = _kpi(_apply_haircut(float(offer_price), haircut_percent), float(cost_total))

    out_reason = None
    if float(cost_total) == 0:
        out_reason = "ZERO_COST"

    return {
        "product_id": produit.id,
        "from_lot": False,
        "a_ete_achete": bool(produit.a_ete_achete),
        "haircut_percent": haircut_percent,
        "cost_total": float(cost_total),
        "scenarios": scenarios,
        "reason": out_reason,
    }