from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow import validate


# =========================
# READ
# =========================
class OtherChargesReadSchema(Schema):
    id = fields.Int(dump_only=True)

    intitule = fields.Str(required=True)
    montant = fields.Float(required=True)

    produit_id = fields.Int(allow_none=True)
    lot_id = fields.Int(allow_none=True)


# =========================
# CREATE
# =========================
class OtherChargesCreateSchema(Schema):
    intitule = fields.Str(required=True, validate=validate.Length(min=1))
    montant = fields.Float(required=True)

    produit_id = fields.Int(required=False, allow_none=True)
    lot_id = fields.Int(required=False, allow_none=True)

    @validates_schema
    def validate_target(self, data, **kwargs):
        produit_id = data.get("produit_id")
        lot_id = data.get("lot_id")

        # EXACTEMENT UN des deux
        if bool(produit_id) == bool(lot_id):
            raise ValidationError(
                "Exactly one of produit_id or lot_id must be provided."
            )


# =========================
# PATCH
# =========================
class OtherChargesPatchSchema(Schema):
    intitule = fields.Str(required=False, validate=validate.Length(min=1))
    montant = fields.Float(required=False)

    produit_id = fields.Int(required=False, allow_none=True)
    lot_id = fields.Int(required=False, allow_none=True)

    @validates_schema
    def validate_target(self, data, **kwargs):
        # On vérifie seulement si l’un des deux est modifié
        if "produit_id" in data or "lot_id" in data:
            produit_id = data.get("produit_id")
            lot_id = data.get("lot_id")

            if bool(produit_id) == bool(lot_id):
                raise ValidationError(
                    "Exactly one of produit_id or lot_id must be provided."
                )


# =========================
# FILTERS (GET list)
# =========================
class OtherChargesFilterSchema(Schema):
    produit_id = fields.Int(required=False)
    lot_id = fields.Int(required=False)

    page = fields.Int(required=False, validate=validate.Range(min=1))
    page_size = fields.Int(required=False, validate=validate.Range(min=1, max=200))

    order_by = fields.Str(required=False)
    order_dir = fields.Str(required=False, validate=validate.OneOf(["asc", "desc"]))
