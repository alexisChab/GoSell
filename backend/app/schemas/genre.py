from marshmallow import Schema, fields, validate


# -------------------------
# OUT (responses)
# -------------------------
class GenreReadSchema(Schema):
    """Ce que renvoie l'API pour un genre."""
    id = fields.Int(dump_only=True)
    intitule = fields.Str(dump_only=True)
    categorie_id = fields.Int(dump_only=True)


# -------------------------
# IN (create / update)
# -------------------------
class GenreCreateSchema(Schema):
    """Payload POST /genres"""
    intitule = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    categorie_id = fields.Int(required=True)


class GenrePatchSchema(Schema):
    """Payload PATCH /genres/<id> (tout optionnel)."""
    intitule = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=255),
    )
    categorie_id = fields.Int(required=False, allow_none=True)


# -------------------------
# Filters (GET list)
# -------------------------
class GenreFilterSchema(Schema):
    """
    Query params GET /genres?... (pagination / tri / filtres)
    """
    search = fields.Str(load_default=None)          # filtre sur intitule (ilike)
    categorie_id = fields.Int(load_default=None)    # filtre exact

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=200))

    order_by = fields.Str(
        load_default="id",
        validate=validate.OneOf(["id", "intitule", "categorie_id"]),
    )
    order_dir = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )
