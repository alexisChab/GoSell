# app/schemas/where_sell.py
from marshmallow import Schema, fields, validate


# -------------------------
# OUT (responses)
# -------------------------
class WhereSellReadSchema(Schema):
    produit_id = fields.Int(dump_only=True)
    plateforme_id = fields.Int(dump_only=True)
    lien = fields.Str(dump_only=True, allow_none=True)


# -------------------------
# IN (create)
# -------------------------
class WhereSellCreateSchema(Schema):
    """
    Payload POST /ou-ventes
    Crée le lien (produit_id, plateforme_id) et optionnellement un lien (URL).
    """
    produit_id = fields.Int(required=True)
    plateforme_id = fields.Int(required=True)
    lien = fields.Str(required=False, allow_none=True, validate=validate.Length(max=2048))


# -------------------------
# IN (patch)
# -------------------------
class WhereSellPatchSchema(Schema):
    """
    Payload PATCH /ou-ventes/<produit_id>/<plateforme_id>
    Sur une table pivot, on patch généralement seulement les champs non-PK (ici lien).
    """
    lien = fields.Str(required=False, allow_none=True, validate=validate.Length(max=2048))


# -------------------------
# Filters (GET list)
# -------------------------
class WhereSellFilterSchema(Schema):
    """
    Query params GET /ou-ventes?produit_id=...&plateforme_id=...
    """
    produit_id = fields.Int(load_default=None)
    plateforme_id = fields.Int(load_default=None)

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=200))

