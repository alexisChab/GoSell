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