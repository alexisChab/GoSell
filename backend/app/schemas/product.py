from marshmallow import Schema, fields, validate, EXCLUDE
from app.schemas.stock import StockReadSchema
class ProductReadSchema(Schema):
    """Réponse GET produit."""
    id = fields.Int(dump_only=True)

    name = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)

    en_vente = fields.Bool(dump_only=True)
    est_vendu = fields.Bool(dump_only=True)
    a_ete_achete = fields.Bool(dump_only=True)

    prix_achat = fields.Float(dump_only=True, allow_none=True)
    prix_vente = fields.Float(dump_only=True, allow_none=True)
    prix_min_espere = fields.Float(dump_only=True, allow_none=True)
    prix_max_espere = fields.Float(dump_only=True, allow_none=True)

    date_mise_en_vente = fields.Date(dump_only=True, allow_none=True)

    user_id = fields.Int(dump_only=True)

class ProductCreateSchema(Schema):
    """Payload POST produit."""
    name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(allow_none=True)

    en_vente = fields.Bool(load_default=False)
    est_vendu = fields.Bool(load_default=False)
    a_ete_achete = fields.Bool(load_default=False)

    prix_achat = fields.Float(allow_none=True, load_default=0)
    prix_vente = fields.Float(allow_none=True)
    prix_min_espere = fields.Float(allow_none=True, load_default=0)
    prix_max_espere = fields.Float(allow_none=True, load_default=0)

    date_mise_en_vente = fields.Date(allow_none=True)

class ProductUpdateSchema(Schema):
    """Payload attendu pour modifier un produit (PATCH)"""

    nom = fields.Str(validate=validate.Length(min=1))
    description = fields.Str(allow_none=True)

    en_vente = fields.Bool()
    est_vendu = fields.Bool()
    a_ete_achete = fields.Bool()

    prix_achat = fields.Float(allow_none=True)
    prix_vente = fields.Float(allow_none=True)
    prix_min_espere = fields.Float(allow_none=True)
    prix_max_espere = fields.Float(allow_none=True)

    date_mise_en_vente = fields.Date(allow_none=True)

class ProductDeleteResponseSchema(Schema):
    """
    Réponse standardisée d'un DELETE.
    """
    ok = fields.Bool(dump_only=True)
    deleted_product_id = fields.Int(dump_only=True)
    message = fields.Str(dump_only=True)

    class ProductToStockRequestSchema(Schema):
        """
        Payload pour une route du style:
          POST /products/<id>/to-stock
        """
        # Champs optionnels "métier" pour enrichir l'entrée Stock
        note = fields.Str(allow_none=True)
        date_entree_stock = fields.Date(allow_none=True)

        # si tu veux copier/forcer une valeur estimée (collection, etc.)
        valeur_estimee = fields.Float(allow_none=True)

        # si tu veux garder une trace du "pourquoi j'arrête la vente"
        raison = fields.Str(allow_none=True)

        # si tu veux forcer l'arrêt de la vente au moment du transfert (souvent oui)
        stop_sale = fields.Bool(load_default=True)

        class Meta:
            unknown = EXCLUDE

class ProductToStockResponseSchema(Schema):
    """
    Réponse de la route produit->stock :
    - confirme la suppression côté produit
    - renvoie l'objet stock créé
    """
    ok = fields.Bool(dump_only=True)
    moved_product_id = fields.Int(dump_only=True)
    stock_item = fields.Nested(StockReadSchema, dump_only=True)
    message = fields.Str(dump_only=True)

class ProductFilterSchema(Schema):
    """
    Schéma de filtrage pour GET /products
    """


    search = fields.Str(allow_none=True)

    # Filtres prix (sliders front)
    prix_achat_min = fields.Float(allow_none=True)
    prix_achat_max = fields.Float(allow_none=True)

    prix_vente_min = fields.Float(allow_none=True)
    prix_vente_max = fields.Float(allow_none=True)

    prix_min_espere_min = fields.Float(allow_none=True)
    prix_min_espere_max = fields.Float(allow_none=True)

    prix_max_espere_min = fields.Float(allow_none=True)
    prix_max_espere_max = fields.Float(allow_none=True)

    # États métier
    en_vente = fields.Bool(allow_none=True)
    est_vendu = fields.Bool(allow_none=True)
    a_ete_achete = fields.Bool(allow_none=True)

    # Dates
    date_mise_en_vente_from = fields.Date(allow_none=True)
    date_mise_en_vente_to = fields.Date(allow_none=True)

    # Pagination
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))

    # Tri
    order_by = fields.Str(
        validate=validate.OneOf([
            "date_mise_en_vente",
            "prix_vente",
            "prix_achat",
            "nom"
        ]),
        allow_none=True
    )
    order_dir = fields.Str(
        validate=validate.OneOf(["asc", "desc"]),
        load_default="desc"
    )

    class Meta:
        unknown = EXCLUDE