# app/schemas/product_type.py
from marshmallow import Schema, fields, validate


# -------------------------
# OUT (responses)
# -------------------------
class ProductTypeReadSchema(Schema):
    """Ce que renvoie l'API pour un type de produit."""
    id = fields.Int(dump_only=True)
    nom = fields.Str(dump_only=True)
    genre_id = fields.Int(dump_only=True)


# -------------------------
# IN (create / update)
# -------------------------
class ProductTypeCreateSchema(Schema):
    """Payload POST /type-produits"""
    nom = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    genre_id = fields.Int(required=True)


class ProductTypePatchSchema(Schema):
    """Payload PATCH /type-produits/<id> (tout optionnel)."""
    nom = fields.Str(required=False, allow_none=True, validate=validate.Length(min=1, max=255))
    genre_id = fields.Int(required=False, allow_none=True)


# -------------------------
# Filters (GET list)
# -------------------------
class ProductTypeFilterSchema(Schema):
    """
    Query params GET /type-produits?... (pagination / tri / filtres)
    """
    search = fields.Str(load_default=None)       # filtre ilike sur nom
    genre_id = fields.Int(load_default=None)     # filtre exact

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=200))

    order_by = fields.Str(
        load_default="id",
        validate=validate.OneOf(["id", "nom", "genre_id"]),
    )
    order_dir = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )
