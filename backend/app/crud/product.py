from sqlalchemy import select, and_, func
from app.models.product import Produit
from app.db.deps import db
from app.models.lot_produit import LotProduit
from app.models.delivery_charges import DeliveryCharges
from app.models.other_charges import OtherCharges

def get_products_for_user(user_id: int, filters: dict):
    """
    Retourne la liste des produits de l'utilisateur connecté,
    avec filtres/pagination/tri appliqués.
    """
    conditions = [Produit.user_id == user_id]

    if filters.get("search"):
        conditions.append(Produit.nom.ilike(f"%{filters['search']}%"))

    for flag in ("en_vente", "est_vendu", "a_ete_achete"):
        if filters.get(flag) is not None:
            conditions.append(getattr(Produit, flag) == filters[flag])


    def add_range(col, min_key, max_key):
        if filters.get(min_key) is not None:
            conditions.append(col >= filters[min_key])
        if filters.get(max_key) is not None:
            conditions.append(col <= filters[max_key])

    add_range(Produit.prix_achat, "prix_achat_min", "prix_achat_max")
    add_range(Produit.prix_vente, "prix_vente_min", "prix_vente_max")
    add_range(Produit.prix_min_espere, "prix_min_espere_min", "prix_min_espere_max")
    add_range(Produit.prix_max_espere, "prix_max_espere_min", "prix_max_espere_max")


    if filters.get("date_mise_en_vente_from") is not None:
        conditions.append(Produit.date_mise_en_vente >= filters["date_mise_en_vente_from"])
    if filters.get("date_mise_en_vente_to") is not None:
        conditions.append(Produit.date_mise_en_vente <= filters["date_mise_en_vente_to"])


    order_by = filters.get("order_by") or "id"
    order_dir = filters.get("order_dir", "desc")
    col = getattr(Produit, order_by, Produit.id)
    col = col.desc() if order_dir == "desc" else col.asc()

    # pagination
    page = filters.get("page", 1)
    page_size = filters.get("page_size", 20)
    offset = (page - 1) * page_size

    stmt = (
        select(Produit)
        .where(and_(*conditions))
        .order_by(col)
        .offset(offset)
        .limit(page_size)
    )

    return db().execute(stmt).scalars().all()


def get_product_for_user_by_id(user_id: int, product_id: int):
    """
    Retourne un produit si et seulement si il appartient à user_id.
    Anti-leak : si pas trouvé/ pas à lui => None.
    """
    stmt = select(Produit).where(
        Produit.id == product_id,
        Produit.user_id == user_id
    )
    return db().execute(stmt).scalars().first()

class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


def create_product(user_id: int, data: dict) -> Produit:
    """
    Crée un produit appartenant à user_id.
    data vient du ProductCreateSchema.load(...)
    """
    session = db()

    produit = Produit(
        nom=data["nom"],
        description=data.get("description"),

        en_vente=data.get("en_vente", False),
        est_vendu=data.get("est_vendu", False),
        a_ete_achete=data.get("a_ete_achete", False),

        prix_achat=data.get("prix_achat", 0),
        prix_vente=data.get("prix_vente"),
        prix_min_espere=data.get("prix_min_espere", 0),
        prix_max_espere=data.get("prix_max_espere", 0),

        date_mise_en_vente=data.get("date_mise_en_vente"),

        user_id=user_id,
    )

    session.add(produit)
    session.commit()
    session.refresh(produit)
    return produit


def delete_product(user_id: int, product_id: int) -> None:
    """
    Supprime un produit si et seulement s'il appartient à user_id.
    Anti-leak: si pas à lui => NotFound (ou Forbidden si tu préfères).
    """
    session = db()

    stmt = select(Produit).where(Produit.id == product_id)
    produit = session.execute(stmt).scalars().first()

    if not produit:
        raise NotFoundError("Produit introuvable")

    if produit.user_id != user_id:
        # Option anti-leak recommandée:
        raise NotFoundError("Produit introuvable")
        # Option alternative:
        # raise ForbiddenError("Accès interdit")

    session.delete(produit)
    session.commit()

def update_product(user_id: int, product_id: int, data: dict) -> Produit:
    """
    PATCH partiel d'un produit appartenant à user_id.
    data vient de ProductPatchSchema.load(...)
    """
    session = db()

    stmt = select(Produit).where(Produit.id == product_id)
    produit = session.execute(stmt).scalars().first()

    if not produit:
        raise NotFoundError("Produit introuvable")

    if produit.user_id != user_id:
        # anti-leak
        raise NotFoundError("Produit introuvable")

    # champs modifiables (whitelist)
    updatable = {
        "nom",
        "description",
        "en_vente",
        "est_vendu",
        "a_ete_achete",
        "prix_achat",
        "prix_vente",
        "prix_min_espere",
        "prix_max_espere",
        "date_mise_en_vente",
    }

    for key, value in data.items():
        if key in updatable:
            setattr(produit, key, value)

    session.commit()
    session.refresh(produit)
    return produit

def get_product_finance_for_user(user_id: int, product_id: int) -> dict:
    """
    Retourne un dict prêt à être dump par ProductFinanceReadSchema.

    Règles :
    - Si produit appartient pas à user => None (anti-leak) (ou NotFoundError si tu préfères)
    - Si from_lot => pas de calcul profit/cost
    - Sinon bénéfice espéré = prix_median_espere - (cout_achat + frais)
        - si a_ete_achete == False => cout_achat = 0 (GRATUIT)
        - si a_ete_achete == True => cout_achat = produit.prix_achat (sinon PRIX_ACHAT_MANQUANT)
    """
    session = db()

    # 1) Anti-leak : récupérer le produit (ou None)
    stmt = select(Produit).where(
        Produit.id == product_id,
        Produit.user_id == user_id
    )
    produit = session.execute(stmt).scalars().first()
    if not produit:
        return None

    # 2) from_lot ?
    stmt_lot = select(LotProduit.id).where(LotProduit.produit_id == product_id).limit(1)
    from_lot = session.execute(stmt_lot).first() is not None

    # 3) Prix espérés + médian
    pmin = produit.prix_min_espere
    pmax = produit.prix_max_espere

    def median_expected(a, b):
        if a is None and b is None:
            return None
        if a is None:
            return float(b)
        if b is None:
            return float(a)
        return (float(a) + float(b)) / 2.0

    pmed = median_expected(pmin, pmax)

    # 4) Frais (somme SQL)
    delivery_fees = session.execute(
        select(func.coalesce(func.sum(DeliveryCharges.montant), 0))
        .where(DeliveryCharges.produit_id == product_id)
    ).scalar_one()

    other_fees = session.execute(
        select(func.coalesce(func.sum(OtherCharges.montant), 0))
        .where(OtherCharges.produit_id == product_id)
    ).scalar_one()

    delivery_fees = float(delivery_fees or 0)
    other_fees = float(other_fees or 0)
    total_fees = delivery_fees + other_fees

    # 5) Construire le payload (par défaut)
    payload = {
        "produit_id": produit.id,
        "from_lot": bool(from_lot),
        "a_ete_achete": bool(produit.a_ete_achete),
        "prix": {
            "min_espere": None if pmin is None else float(pmin),
            "max_espere": None if pmax is None else float(pmax),
            "median_espere": None if pmed is None else float(pmed),
        },
        "fees": {
            "delivery_fees": delivery_fees,
            "other_fees": other_fees,
            "total_fees": total_fees,
        },
        "costs": {
            "cout_achat": None,
            "cout_total": None,
            "cost_source": None,
        },
        "profit": {
            "benefice_espere": None,
            "is_benefice_espere": None,
            "reason": None,
        },
    }

    # --- règle lot : stop ici ---
    if from_lot:
        payload["profit"]["reason"] = "CALCUL_AU_NIVEAU_DU_LOT"
        return payload

    # --- on veut un bénéfice espéré basé sur le médian ---
    if pmed is None:
        payload["profit"]["reason"] = "PRIX_ESPERES_INSUFFISANTS"
        return payload

    # --- coût achat selon gratuit / acheté ---
    if not produit.a_ete_achete:
        cout_achat = 0.0
        cost_source = "GRATUIT"
    else:
        if produit.prix_achat is None:
            payload["profit"]["reason"] = "PRIX_ACHAT_MANQUANT"
            return payload
        cout_achat = float(produit.prix_achat)
        cost_source = "PRODUIT_PRIX_ACHAT"

    cout_total = cout_achat + total_fees
    benefice_espere = float(pmed) - cout_total

    payload["costs"]["cout_achat"] = cout_achat
    payload["costs"]["cout_total"] = cout_total
    payload["costs"]["cost_source"] = cost_source

    payload["profit"]["benefice_espere"] = benefice_espere
    payload["profit"]["is_benefice_espere"] = benefice_espere > 0

    return payload
