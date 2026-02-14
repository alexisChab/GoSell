from marshmallow import Schema, fields
from marshmallow import validate


# =========================
# READ
# =========================
class DeliveryChargesReadSchema(Schema):
    id = fields.Int(dump_only=True)

    montant = fields.Float(required=True)
    produit_id = fields.Int(required=True)

    lot_id = fields.Int(allow_none=True)
    societe_id = fields.Int(allow_none=True)


# =========================
# CREATE
# =========================
class DeliveryChargesCreateSchema(Schema):
    montant = fields.Float(required=True, validate=validate.Range(min=0))
    produit_id = fields.Int(required=True)

    lot_id = fields.Int(required=False, allow_none=True)
    societe_id = fields.Int(required=False, allow_none=True)


# =========================
# PATCH
# =========================
class DeliveryChargesPatchSchema(Schema):
    montant = fields.Float(required=False, validate=validate.Range(min=0))
    # En général on évite de patch produit_id (ça change la “cible”)
    # mais si tu veux l’autoriser, passe required=False.
    produit_id = fields.Int(required=False)

    lot_id = fields.Int(required=False, allow_none=True)
    societe_id = fields.Int(required=False, allow_none=True)


# =========================
# FILTERS (GET list)
# =========================
class DeliveryChargesFilterSchema(Schema):
    produit_id = fields.Int(required=False)
    lot_id = fields.Int(required=False)
    societe_id = fields.Int(required=False)

    page = fields.Int(required=False, validate=validate.Range(min=1))
    page_size = fields.Int(required=False, validate=validate.Range(min=1, max=200))

    order_by = fields.Str(required=False)
    order_dir = fields.Str(required=False, validate=validate.OneOf(["asc", "desc"]))
