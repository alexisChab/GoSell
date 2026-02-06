from sqlalchemy import select, and_
from app.models.product import Produit
from app.db.deps import db

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