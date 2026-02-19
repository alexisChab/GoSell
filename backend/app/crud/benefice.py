from __future__ import annotations

from sqlalchemy import select, and_, func, case, literal, cast, Float
from sqlalchemy.orm import Session
from collections import defaultdict
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

def get_risk_products_for_user(user_id: int, filters: dict) -> dict:
    session: Session = db()

    limit = int(filters.get("limit", 50))
    only_en_vente = bool(filters.get("only_en_vente", True))
    include_lot_products = bool(filters.get("include_lot_products", False))
    threshold_multiple = float(filters.get("threshold_multiple", 1.0))

    categorie_id = filters.get("categorie_id")
    genre_id = filters.get("genre_id")
    type_produit_id = filters.get("type_produit_id")
    need_taxonomy_join = any(x is not None for x in (categorie_id, genre_id, type_produit_id))

    conds = [Produit.user_id == user_id]
    if only_en_vente:
        conds.append(Produit.en_vente == True)  # noqa: E712

    stmt = select(Produit).where(and_(*conds))

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

    # (optionnel) petit tri : les plus chers d'abord pour remonter les plus “dangereux”
    stmt = stmt.order_by(Produit.id.desc()).limit(limit * 3)

    produits = session.execute(stmt).scalars().all()

    items = []
    for p in produits:
        ctx = _get_product_cost_context_for_user(session, user_id, p.id)
        if ctx is None:
            continue

        # lot ?
        if ctx["from_lot"]:
            if not include_lot_products:
                continue
            items.append({
                "product_id": p.id,
                "nom": getattr(p, "nom", None),
                "from_lot": True,
                "median_expected": ctx["pmed"],
                "cost_total": None,
                "profit_amount": None,
                "multiple": None,
                "risk_level": "LOSS",
                "reason": "CALCUL_AU_NIVEAU_DU_LOT",
            })
            continue

        # coût calculable ?
        if ctx["cost_total"] is None:
            items.append({
                "product_id": p.id,
                "nom": getattr(p, "nom", None),
                "from_lot": False,
                "median_expected": ctx["pmed"],
                "cost_total": None,
                "profit_amount": None,
                "multiple": None,
                "risk_level": "LOSS",
                "reason": ctx["reason"],
            })
            continue

        cost_total = float(ctx["cost_total"])
        median = ctx["pmed"]

        # médian calculable ?
        if median is None:
            items.append({
                "product_id": p.id,
                "nom": getattr(p, "nom", None),
                "from_lot": False,
                "median_expected": None,
                "cost_total": cost_total,
                "profit_amount": None,
                "multiple": None,
                "risk_level": "LOSS",
                "reason": "PRIX_ESPERES_INSUFFISANTS",
            })
            continue

        median = float(median)
        profit_amount = median - cost_total

        if cost_total == 0:
            multiple = None
            reason = "ZERO_COST"
        else:
            multiple = median / cost_total
            reason = None

        # filtre risk: multiple < threshold (par défaut 1.0)
        if multiple is not None and multiple >= threshold_multiple:
            continue

        risk_level = "LOSS" if profit_amount < 0 else "LOW_MARGIN"

        items.append({
            "product_id": p.id,
            "nom": getattr(p, "nom", None),
            "from_lot": False,
            "median_expected": median,
            "cost_total": cost_total,
            "profit_amount": float(profit_amount),
            "multiple": None if multiple is None else float(multiple),
            "risk_level": risk_level,
            "reason": reason,
        })

        if len(items) >= limit:
            break

    return {"items": items, "count": len(items)}

def get_best_types_for_user(user_id: int, filters: dict) -> dict:
    session: Session = db()

    min_multiple = float(filters.get("min_multiple", 1.5))
    min_count = int(filters.get("min_count", 3))
    only_en_vente = bool(filters.get("only_en_vente", True))
    exclude_lot_products = bool(filters.get("exclude_lot_products", True))
    max_avg_cost_total = filters.get("max_avg_cost_total")
    categorie_id = filters.get("categorie_id")
    genre_id = filters.get("genre_id")
    limit = int(filters.get("limit", 50))

    # 1) récupérer couples (produit_id, type_id) filtrés taxonomie si demandé
    stmt = (
        select(Produit.id, ProductType.id, ProductType.nom)
        .join(ProduitTypeProduit, ProduitTypeProduit.produit_id == Produit.id)
        .join(ProductType, ProductType.id == ProduitTypeProduit.type_produit_id)
        .where(Produit.user_id == user_id)
    )

    if only_en_vente:
        stmt = stmt.where(Produit.en_vente == True)  # noqa: E712

    if genre_id is not None or categorie_id is not None:
        stmt = stmt.join(Genre, Genre.id == ProductType.genre_id)
    if categorie_id is not None:
        stmt = stmt.join(Category, Category.id == Genre.categorie_id)

    if genre_id is not None:
        stmt = stmt.where(Genre.id == int(genre_id))
    if categorie_id is not None:
        stmt = stmt.where(Category.id == int(categorie_id))

    rows = session.execute(stmt).all()

    # 2) agrégation par type
    by_type = defaultdict(lambda: {
        "type_produit_id": None,
        "type_produit_nom": None,
        "count_products": 0,
        "count_profitable": 0,
        "sum_multiple": 0.0,
        "sum_cost_total": 0.0,
        "sum_profit_amount": 0.0,
    })

    for product_id, type_id, type_nom in rows:
        ctx = _get_product_cost_context_for_user(session, user_id, int(product_id))
        if ctx is None:
            continue

        # exclure lot (par défaut)
        if ctx["from_lot"]:
            if exclude_lot_products:
                continue
            else:
                continue  # on ne peut pas calculer un ratio type “propre” au niveau produit

        # cost ok ?
        cost_total = ctx["cost_total"]
        if cost_total is None:
            continue

        # median ok ?
        median = ctx["pmed"]
        if median is None:
            continue

        cost_total = float(cost_total)
        median = float(median)

        # multiple
        if cost_total == 0:
            # gratuit+0 frais => multiple infini, ça fausse : on ignore
            continue

        multiple = median / cost_total
        profit_amount = median - cost_total

        d = by_type[int(type_id)]
        d["type_produit_id"] = int(type_id)
        d["type_produit_nom"] = type_nom
        d["count_products"] += 1
        d["sum_multiple"] += float(multiple)
        d["sum_cost_total"] += float(cost_total)
        d["sum_profit_amount"] += float(profit_amount)
        if multiple >= min_multiple:
            d["count_profitable"] += 1

    # 3) construire sortie + filtres min_count / max_avg_cost_total
    items = []
    for type_id, d in by_type.items():
        n = d["count_products"]
        if n < min_count:
            continue

        avg_multiple = d["sum_multiple"] / n
        avg_cost = d["sum_cost_total"] / n
        avg_profit = d["sum_profit_amount"] / n
        success_rate = d["count_profitable"] / n

        if avg_multiple < min_multiple:
            continue
        if max_avg_cost_total is not None and avg_cost > float(max_avg_cost_total):
            continue

        items.append({
            "type_produit_id": d["type_produit_id"],
            "type_produit_nom": d["type_produit_nom"],
            "count_products": n,
            "count_profitable": d["count_profitable"],
            "success_rate": float(success_rate),
            "avg_multiple_median": float(avg_multiple),
            "avg_cost_total": float(avg_cost),
            "avg_profit_amount": float(avg_profit),
        })

    # tri: meilleurs d'abord
    items.sort(key=lambda x: (x["avg_multiple_median"], x["success_rate"], x["count_products"]), reverse=True)
    items = items[:limit]

    return {
        "filters": {
            "min_multiple": min_multiple,
            "min_count": min_count,
            "only_en_vente": only_en_vente,
            "exclude_lot_products": exclude_lot_products,
            "max_avg_cost_total": max_avg_cost_total,
            "categorie_id": categorie_id,
            "genre_id": genre_id,
            "limit": limit,
        },
        "items": items,
        "count": len(items),
    }

def get_benefice_breakdown_for_user(user_id: int, filters: dict) -> dict:
    session: Session = db()

    group_by = filters["group_by"]
    include_fees = bool(filters.get("include_fees", True))
    exclude_lot_products = bool(filters.get("exclude_lot_products", True))
    only_en_vente = bool(filters.get("only_en_vente", False))
    only_unsold = bool(filters.get("only_unsold", False))
    min_count = int(filters.get("min_count", 1))
    limit = int(filters.get("limit", 50))

    # ---- fees subqueries (agrégées par produit) ----
    deliv_sq = (
        select(
            DeliveryCharges.produit_id.label("pid"),
            func.coalesce(func.sum(DeliveryCharges.montant), 0.0).label("delivery_fees"),
        )
        .group_by(DeliveryCharges.produit_id)
        .subquery()
    )

    other_sq = (
        select(
            OtherCharges.produit_id.label("pid"),
            func.coalesce(func.sum(OtherCharges.montant), 0.0).label("other_fees"),
        )
        .group_by(OtherCharges.produit_id)
        .subquery()
    )

    fees_expr = (
        func.coalesce(deliv_sq.c.delivery_fees, 0.0) + func.coalesce(other_sq.c.other_fees, 0.0)
        if include_fees
        else literal_column("0.0")
    )

    median = _median_expr(Produit.prix_min_espere, Produit.prix_max_espere)

    # coût achat: gratuit => 0 ; acheté => prix_achat (NULL => ignoré via filtre plus bas)
    cost_achat = case(
        (Produit.a_ete_achete == False, 0.0),  # noqa: E712
        else_=cast(Produit.prix_achat, Float),
    )

    # on ignore les lignes où:
    # - median est NULL (pas de scénario)
    # - produit acheté mais prix_achat NULL (sinon coût impossible)
    # (gratuit ok => cost_achat=0)
    base_conds = [Produit.user_id == user_id]
    if only_en_vente:
        base_conds.append(Produit.en_vente == True)  # noqa: E712
    if only_unsold:
        base_conds.append(Produit.est_vendu == False)  # noqa: E712

    # median doit être non null
    base_conds.append(median.isnot(None))

    # si acheté, prix_achat doit être non null
    base_conds.append(
        case(
            (Produit.a_ete_achete == True, Produit.prix_achat.isnot(None)),  # noqa: E712
            else_=True,
        )
    )

    # exclure produits en lot (par défaut)
    if exclude_lot_products:
        base_conds.append(
            ~select(LotProduit.id).where(LotProduit.produit_id == Produit.id).exists()
        )

    # ---- join taxonomie (toujours, car breakdown par cat/genre/type) ----
    stmt = (
        select()
        .select_from(Produit)
        .join(ProduitTypeProduit, ProduitTypeProduit.produit_id == Produit.id)
        .join(ProductType, ProductType.id == ProduitTypeProduit.type_produit_id)
        .join(Genre, Genre.id == ProductType.genre_id)
        .join(Category, Category.id == Genre.categorie_id)
        .outerjoin(deliv_sq, deliv_sq.c.pid == Produit.id)
        .outerjoin(other_sq, other_sq.c.pid == Produit.id)
        .where(and_(*base_conds))
    )

    # ---- group columns ----
    if group_by == "type_produit":
        group_id_col = ProductType.id
        group_name_col = ProductType.nom
    elif group_by == "genre":
        group_id_col = Genre.id
        group_name_col = Genre.intitule
    else:  # categorie
        group_id_col = Category.id
        group_name_col = Category.intitule

    cost_total_expr = cast(cost_achat, Float) + cast(fees_expr, Float)

    stmt = stmt.with_only_columns(
        group_id_col.label("group_id"),
        group_name_col.label("group_name"),
        func.count(func.distinct(Produit.id)).label("count_products"),
        func.coalesce(func.sum(median), 0.0).label("revenue_expected_median"),
        func.coalesce(func.sum(cost_achat), 0.0).label("cost_products"),
        func.coalesce(func.sum(fees_expr), 0.0).label("fees"),
        func.coalesce(func.sum(cost_total_expr), 0.0).label("cost_total"),
    ).group_by(group_id_col, group_name_col)

    # min_count + tri + limit
    stmt = stmt.having(func.count(func.distinct(Produit.id)) >= min_count)
    stmt = stmt.order_by(func.coalesce(func.sum(median) - func.sum(cost_total_expr), 0.0).desc())
    stmt = stmt.limit(limit)

    rows = session.execute(stmt).all()

    items = []
    for r in rows:
        revenue = float(r.revenue_expected_median or 0.0)
        cost_total = float(r.cost_total or 0.0)
        profit = revenue - cost_total

        avg_multiple = None
        if cost_total > 0:
            avg_multiple = revenue / cost_total

        items.append({
            "group_id": int(r.group_id) if r.group_id is not None else None,
            "group_name": r.group_name,
            "count_products": int(r.count_products or 0),
            "revenue_expected_median": revenue,
            "cost_products": float(r.cost_products or 0.0),
            "fees": float(r.fees or 0.0),
            "cost_total": cost_total,
            "profit_expected_median": float(profit),
            "is_profit_expected_median": profit > 0,
            "avg_multiple_median": None if avg_multiple is None else float(avg_multiple),
        })

    return {
        "group_by": group_by,
        "items": items,
        "count": len(items),
    }