from __future__ import annotations

from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.deps import db
from app.models.lot import Lot
from app.models.lot_produit import LotProduit
from app.models.product import Produit
from app.models.delivery_charges import DeliveryCharges
from app.models.other_charges import OtherCharges

# =========================================================
# GET LIST (scopé par user + filtres + pagination + tri)
# =========================================================

def get_lots_by_user(user_id: int, filters: dict | None = None) -> list[Lot]:
    session: Session = db()
    filters = filters or {}

    conditions = [Lot.user_id == user_id]

    # --------------------
    # Filtres métier
    # --------------------
    if filters.get("date_min"):
        conditions.append(Lot.date_achat >= filters["date_min"])

    if filters.get("date_max"):
        conditions.append(Lot.date_achat <= filters["date_max"])

    if filters.get("prix_min") is not None:
        conditions.append(Lot.prix_total_achat >= filters["prix_min"])

    if filters.get("prix_max") is not None:
        conditions.append(Lot.prix_total_achat <= filters["prix_max"])

    # --------------------
    # Pagination
    # --------------------
    page = int(filters.get("page") or 1)
    page_size = int(filters.get("page_size") or 20)

    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)

    offset = (page - 1) * page_size

    # --------------------
    # Tri sécurisé
    # --------------------
    order_by = (filters.get("order_by") or "id").lower()
    order_dir = (filters.get("order_dir") or "desc").lower()

    allowed_columns = {
        "id": Lot.id,
        "date_achat": Lot.date_achat,
        "prix_total_achat": Lot.prix_total_achat,
        "created_at": Lot.created_at,
        "updated_at": Lot.updated_at,
    }

    column = allowed_columns.get(order_by, Lot.id)

    order_expr = column.asc() if order_dir == "asc" else column.desc()

    stmt = (
        select(Lot)
        .where(and_(*conditions))
        .order_by(order_expr)
        .offset(offset)
        .limit(page_size)
    )

    return session.execute(stmt).scalars().all()


# =========================================================
# GET ONE (scopé par user)
# =========================================================

def get_lot_by_id_for_user(user_id: int, lot_id: int) -> Lot | None:
    session: Session = db()

    stmt = select(Lot).where(
        and_(Lot.id == lot_id, Lot.user_id == user_id)
    )

    return session.execute(stmt).scalars().first()


# =========================================================
# CREATE (user_id injecté depuis JWT)
# =========================================================

def create_lot_for_user(
    user_id: int,
    titre: str | None,
    description: str | None,
    prix_total_achat: float,
    date_achat=None,
) -> Lot:
    session: Session = db()

    item = Lot(
        user_id=user_id,
        titre=titre,
        description=description,
        prix_total_achat=prix_total_achat,
        date_achat=date_achat,
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
# PATCH (user scoped + sécurité totale)
# =========================================================

def patch_lot_for_user(
    user_id: int,
    lot_id: int,
    data: dict,
) -> Lot | None:
    session: Session = db()

    item = get_lot_by_id_for_user(user_id, lot_id)
    if item is None:
        return None

    # Interdire toute modification sensible
    data.pop("user_id", None)
    data.pop("id", None)
    data.pop("created_at", None)
    data.pop("updated_at", None)

    if "titre" in data:
        item.titre = data["titre"]

    if "description" in data:
        item.description = data["description"]

    if "prix_total_achat" in data:
        item.prix_total_achat = data["prix_total_achat"]

    if "date_achat" in data:
        item.date_achat = data["date_achat"]

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    session.refresh(item)
    return item


# =========================================================
# DELETE (user scoped)
# =========================================================

def delete_lot_for_user(user_id: int, lot_id: int) -> bool:
    session: Session = db()

    item = get_lot_by_id_for_user(user_id, lot_id)
    if item is None:
        return False

    session.delete(item)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return True


# =========================================================
# COUNT (utile pour UI pagination)
# =========================================================

def count_lots_for_user(user_id: int) -> int:
    session: Session = db()

    stmt = select(func.count()).select_from(Lot).where(
        Lot.user_id == user_id
    )

    return int(session.execute(stmt).scalar_one())

def _median_expected(pmin, pmax) -> float | None:
    if pmin is None and pmax is None:
        return None
    if pmin is None:
        return float(pmax)
    if pmax is None:
        return float(pmin)
    return (float(pmin) + float(pmax)) / 2.0


def get_lot_finance_for_user(user_id: int, lot_id: int) -> dict | None:
    """
    Retourne un dict prêt à être dump par LotFinanceReadSchema.

    Logique:
    - Anti-leak: lot doit appartenir à user_id
    - achat_lot = lot.prix_total_achat
    - frais_lot = sum(DeliveryCharges.lot_id) + sum(OtherCharges.lot_id)
    - frais_produits = sum(frais livraison + annexe des produits du lot)
    - revenue_vendu = sum(prix_vente * quantite) sur produits vendus
    - revenue_espere_median = sum(median_espere * quantite) sur tous les produits
        - si un produit n'a ni min ni max => PRIX_ESPERES_INSUFFISANTS (et revenue_espere_median/profit null)
    - profit_espere_median = revenue_espere_median - (achat_lot + total_fees)
    """
    session: Session = db()

    # 1) Lot (anti-leak)
    stmt_lot = select(Lot).where(and_(Lot.id == lot_id, Lot.user_id == user_id))
    lot = session.execute(stmt_lot).scalars().first()
    if not lot:
        return None

    achat_lot = float(lot.prix_total_achat or 0.0)

    # 2) Récupérer les produits du lot + quantités
    stmt_rows = (
        select(
            Produit.id,
            Produit.est_vendu,
            Produit.prix_vente,
            Produit.prix_min_espere,
            Produit.prix_max_espere,
            LotProduit.quantite,
        )
        .join(LotProduit, LotProduit.produit_id == Produit.id)
        .where(LotProduit.lot_id == lot_id)
    )
    rows = session.execute(stmt_rows).all()

    # counts
    nb_produits = int(sum((r.quantite or 0) for r in rows))  # nb d'unités au sens quantite
    nb_vendus = int(sum((r.quantite or 0) for r in rows if r.est_vendu))

    # revenue vendu (réel)
    revenue_vendu = 0.0
    for r in rows:
        if r.est_vendu and r.prix_vente is not None:
            revenue_vendu += float(r.prix_vente) * int(r.quantite or 0)

    # revenue espéré médian (attendu)
    revenue_espere_median = 0.0
    missing_expected = False
    for r in rows:
        med = _median_expected(r.prix_min_espere, r.prix_max_espere)
        if med is None:
            # si le lot a des produits sans espérance, tu as demandé un statut clair
            missing_expected = True
            break
        revenue_espere_median += float(med) * int(r.quantite or 0)

    # si lot vide -> revenue espéré = 0 (pas "insuffisant")
    if len(rows) == 0:
        missing_expected = False
        revenue_espere_median = 0.0

    # 3) Frais lot (livraison + annexe au niveau du lot)
    lot_delivery = session.execute(
        select(func.coalesce(func.sum(DeliveryCharges.montant), 0.0))
        .where(DeliveryCharges.lot_id == lot_id)
    ).scalar_one()

    lot_other = session.execute(
        select(func.coalesce(func.sum(OtherCharges.montant), 0.0))
        .where(OtherCharges.lot_id == lot_id)
    ).scalar_one()

    lot_fees = float(lot_delivery or 0.0) + float(lot_other or 0.0)

    # 4) Frais produits (livraison + annexe au niveau produit) pour produits présents dans le lot
    product_ids = [r.id for r in rows]
    produits_fees = 0.0
    if product_ids:
        prod_delivery = session.execute(
            select(func.coalesce(func.sum(DeliveryCharges.montant), 0.0))
            .where(DeliveryCharges.produit_id.in_(product_ids))
        ).scalar_one()

        prod_other = session.execute(
            select(func.coalesce(func.sum(OtherCharges.montant), 0.0))
            .where(OtherCharges.produit_id.in_(product_ids))
        ).scalar_one()

        produits_fees = float(prod_delivery or 0.0) + float(prod_other or 0.0)

    total_fees = lot_fees + produits_fees
    total_cost = achat_lot + total_fees

    # 5) Profit espéré médian
    profit_espere_median = None
    is_profit_espere_median = None
    reason = None

    if missing_expected:
        reason = "PRIX_ESPERES_INSUFFISANTS"
        revenue_espere_median_out = None
    else:
        revenue_espere_median_out = float(revenue_espere_median)
        profit_espere_median = float(revenue_espere_median_out) - float(total_cost)
        is_profit_espere_median = profit_espere_median > 0

    return {
        "lot_id": lot.id,
        "counts": {
            "nb_produits": nb_produits,
            "nb_vendus": nb_vendus,
        },
        "revenue": {
            "revenue_vendu": float(revenue_vendu),
            "revenue_espere_median": revenue_espere_median_out,
        },
        "fees": {
            "lot_other_fees": float(lot_fees),
            "produits_fees": float(produits_fees),
            "total_fees": float(total_fees),
        },
        "costs": {
            "achat_lot": float(achat_lot),
            "total_cost": float(total_cost),
        },
        "profit": {
            "profit_espere_median": profit_espere_median,
            "is_profit_espere_median": is_profit_espere_median,
            "reason": reason,
        },
    }
