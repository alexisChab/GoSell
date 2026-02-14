from marshmallow import Schema, fields, validate


# =========================
# READ
# =========================
class LotProduitReadSchema(Schema):
    id = fields.Int(dump_only=True)

    lot_id = fields.Int(required=True)
    produit_id = fields.Int(required=True)

    quantite = fields.Int(required=True)

    allocation_prix_achat = fields.Float(allow_none=True)
    allocation_frais = fields.Float(allow_none=True)
    allocation_methode = fields.Str(allow_none=True)


# =========================
# CREATE
# =========================
class LotProduitCreateSchema(Schema):
    lot_id = fields.Int(required=True)
    produit_id = fields.Int(required=True)

    # si non fourni, ton modèle met default=1 (mais on valide quand même)
    quantite = fields.Int(required=False, validate=validate.Range(min=1))

    allocation_prix_achat = fields.Float(required=False, allow_none=True)
    allocation_frais = fields.Float(required=False, allow_none=True)

    allocation_methode = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            ["manual", "equal", "weighted_expected", "weighted_real", "other"]
        ),
    )


# =========================
# PATCH
# =========================
class LotProduitPatchSchema(Schema):
    # On ne patch PAS lot_id / produit_id (sinon tu casses l'unicité & les FK)
    quantite = fields.Int(required=False, validate=validate.Range(min=1))

    allocation_prix_achat = fields.Float(required=False, allow_none=True)
    allocation_frais = fields.Float(required=False, allow_none=True)

    allocation_methode = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(
            ["manual", "equal", "weighted_expected", "weighted_real", "other"]
        ),
    )


# =========================
# FILTERS (GET list)
# =========================
class LotProduitFilterSchema(Schema):
    lot_id = fields.Int(required=False)
    produit_id = fields.Int(required=False)

    page = fields.Int(required=False, validate=validate.Range(min=1))
    page_size = fields.Int(required=False, validate=validate.Range(min=1, max=200))

    order_by = fields.Str(required=False)
    order_dir = fields.Str(required=False, validate=validate.OneOf(["asc", "desc"]))
