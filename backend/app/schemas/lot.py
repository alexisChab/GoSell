from marshmallow import Schema, fields, validate


# =========================
# READ
# =========================

class LotReadSchema(Schema):
    id = fields.Int(dump_only=True)

    user_id = fields.Int(required=True)

    titre = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)

    prix_total_achat = fields.Float(required=True)

    date_achat = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


# =========================
# CREATE
# =========================

class LotCreateSchema(Schema):
    titre = fields.Str(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)

    prix_total_achat = fields.Float(
        required=True,
        validate=validate.Range(min=0)
    )

    date_achat = fields.DateTime(required=False, allow_none=True)


# =========================
# PATCH
# =========================

class LotPatchSchema(Schema):
    titre = fields.Str(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)

    prix_total_achat = fields.Float(
        required=False,
        validate=validate.Range(min=0),
    )

    date_achat = fields.DateTime(required=False)


# =========================
# FILTERS (GET list)
# =========================

class LotFilterSchema(Schema):
    user_id = fields.Int(required=False)

    date_min = fields.DateTime(required=False)
    date_max = fields.DateTime(required=False)

    page = fields.Int(required=False, validate=validate.Range(min=1))
    page_size = fields.Int(required=False, validate=validate.Range(min=1, max=200))

    order_by = fields.Str(required=False)
    order_dir = fields.Str(required=False, validate=validate.OneOf(["asc", "desc"]))


class LotPatchSchema(Schema):
    titre = fields.Str(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)

    prix_total_achat = fields.Float(
        required=False,
        validate=validate.Range(min=0)
    )

    date_achat = fields.DateTime(required=False)

    class Meta:
        ordered = True

class LotFilterSchema(Schema):
    # filtres métier
    date_min = fields.DateTime(required=False)
    date_max = fields.DateTime(required=False)

    prix_min = fields.Float(required=False)
    prix_max = fields.Float(required=False)

    # pagination
    page = fields.Int(required=False, validate=validate.Range(min=1))
    page_size = fields.Int(required=False, validate=validate.Range(min=1, max=200))

    # tri
    order_by = fields.Str(required=False)
    order_dir = fields.Str(required=False, validate=validate.OneOf(["asc", "desc"]))
