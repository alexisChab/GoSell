from marshmallow import Schema, fields, validate, EXCLUDE, validates_schema, ValidationError


class PlatformReadSchema(Schema):
    id = fields.Int(dump_only=True)

    nom = fields.Str(dump_only=True)
    frais_supp_eur  = fields.Float(dump_only=True, allow_none=True)
    pourcentage_vente = fields.Float(dump_only=True, allow_none=True)
    lien_homepage = fields.Str(dump_only=True, allow_none=True)

    created_at = fields.DateTime(dump_only=True, allow_none=True)

    class Meta:
        unknown = EXCLUDE

class PlatformFilterSchema(Schema):
    # search sur nom
    search = fields.Str(load_default=None)

    # ranges (optionnels)
    frais_supp_eur_min = fields.Float(allow_none=True, load_default=None)
    frais_supp_eur_max = fields.Float(allow_none=True, load_default=None)

    pourcentage_vente_min = fields.Float(allow_none=True, load_default=None)
    pourcentage_vente_max = fields.Float(allow_none=True, load_default=None)

    # tri + pagination
    order_by = fields.Str(load_default="id")
    order_dir = fields.Str(load_default="asc", validate=validate.OneOf(["asc", "desc"]))

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=200))

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_filters(self, data, **kwargs):
        # >= 0
        for k in (
            "frais_supp_eur_min",
            "frais_supp_eur_max",
            "pourcentage_vente_min",
            "pourcentage_vente_max",
        ):
            if data.get(k) is not None and data[k] < 0:
                raise ValidationError("La valeur ne peut pas être négative.", field_name=k)

        # min <= max
        if data.get("frais_supp_eur_min") is not None and data.get("frais_supp_eur_max") is not None:
            if data["frais_supp_eur_min"] > data["frais_supp_eur_max"]:
                raise ValidationError(
                    "frais_supp_eur_min ne peut pas être > frais_supp_eur_max.",
                    field_name="frais_supp_eur_min",
                )

        if data.get("pourcentage_vente_min") is not None and data.get("pourcentage_vente_max") is not None:
            if data["pourcentage_vente_min"] > data["pourcentage_vente_max"]:
                raise ValidationError(
                    "pourcentage_vente_min ne peut pas être > pourcentage_vente_max.",
                    field_name="pourcentage_vente_min",
                )

        # order_by whitelist
        allowed_order_by = {"id", "nom", "frais_supp_eur", "pourcentage_vente", "lien_homepage"}
        if data.get("order_by") not in allowed_order_by:
            raise ValidationError(
                f"order_by invalide (autorisés: {', '.join(sorted(allowed_order_by))})",
                field_name="order_by",
            )

class PlatformCreateSchema(Schema):
    """
    Payload POST /api/platforms
    """

    nom = fields.Str(required=True, validate=validate.Length(min=1))

    frais_supp_eur = fields.Float(allow_none=True, load_default=0)
    pourcentage_vente = fields.Float(allow_none=True, load_default=0)

    lien_homepage = fields.Str(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_platform(self, data, **kwargs):
        if data.get("frais_supp_eur") is not None and data["frais_supp_eur"] < 0:
            raise ValidationError(
                "frais_supp_eur ne peut pas être négatif.",
                field_name="frais_supp_eur",
            )

        if data.get("pourcentage_vente") is not None:
            if data["pourcentage_vente"] < 0 or data["pourcentage_vente"] > 100:
                raise ValidationError(
                    "pourcentage_vente doit être entre 0 et 100.",
                    field_name="pourcentage_vente",
                )

class PlatformDeleteResponseSchema(Schema):
    ok = fields.Bool(dump_only=True)
    deleted_platform_id = fields.Int(dump_only=True)

class PlatformPatchSchema(Schema):
    nom = fields.Str(
        required=False,
        validate=validate.Length(min=1)
    )

    frais_supp_eur = fields.Float(
        required=False,
        allow_none=True
    )

    pourcentage_vente = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0)
    )

    lien_homepage = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1)
    )