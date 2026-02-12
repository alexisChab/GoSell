from marshmallow import Schema, fields


# -------------------------
# OUT (responses)
# -------------------------
class ProduitTypeProduitReadSchema(Schema):
    produit_id = fields.Int(dump_only=True)
    type_produit_id = fields.Int(dump_only=True)


# -------------------------
# IN (create)
# -------------------------
class ProduitTypeProduitCreateSchema(Schema):
    """
    Payload POST /produit-type-produits
    Ajoute un lien entre un produit et un type_produit.
    """
    produit_id = fields.Int(required=True)
    type_produit_id = fields.Int(required=True)


# -------------------------
# (optionnel) Filters (GET list)
# -------------------------
class ProduitTypeProduitFilterSchema(Schema):
    """
    Query params GET /produit-type-produits?produit_id=...&type_produit_id=...
    """
    produit_id = fields.Int(load_default=None)
    type_produit_id = fields.Int(load_default=None)

    page = fields.Int(load_default=1)
    page_size = fields.Int(load_default=20)
