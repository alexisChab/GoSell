from marshmallow import Schema, fields, validate, EXCLUDE, validates_schema, ValidationError


class StockReadSchema(Schema):
    id = fields.Int(dump_only=True)

    nom = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)
    localisation = fields.Str(dump_only=True, allow_none=True)

    a_ete_achete = fields.Bool(dump_only=True, allow_none=True)

    # modèle: Float nullable
    prix_achat = fields.Float(dump_only=True, allow_none=True)

    # modèle: DateTime nullable
    created_at = fields.DateTime(dump_only=True, allow_none=True)

    user_id = fields.Int(dump_only=True)

    class Meta:
        unknown = EXCLUDE


class StockFilterSchema(Schema):
    """
    Query params pour GET /api/stock
    (filtres compatibles avec le modèle Stock)
    """

    # recherche sur "nom" (ilike dans le CRUD)
    search = fields.Str(load_default=None)

    a_ete_achete = fields.Bool(allow_none=True, load_default=None)

    # ranges sur prix_achat (Float)
    prix_achat_min = fields.Float(allow_none=True, load_default=None)
    prix_achat_max = fields.Float(allow_none=True, load_default=None)

    # created_at (DateTime)
    created_at_from = fields.DateTime(allow_none=True, load_default=None)
    created_at_to = fields.DateTime(allow_none=True, load_default=None)

    # tri + pagination
    order_by = fields.Str(load_default="created_at")
    order_dir = fields.Str(load_default="desc", validate=validate.OneOf(["asc", "desc"]))

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=200))

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_filters(self, data, **kwargs):
        # prix >= 0
        for k in ("prix_achat_min", "prix_achat_max"):
            if data.get(k) is not None and data[k] < 0:
                raise ValidationError("prix_achat ne peut pas être négatif.", field_name=k)

        # min <= max
        if data.get("prix_achat_min") is not None and data.get("prix_achat_max") is not None:
            if data["prix_achat_min"] > data["prix_achat_max"]:
                raise ValidationError(
                    "prix_achat_min ne peut pas être > prix_achat_max.",
                    field_name="prix_achat_min",
                )

        # created_at_from <= created_at_to
        if data.get("created_at_from") is not None and data.get("created_at_to") is not None:
            if data["created_at_from"] > data["created_at_to"]:
                raise ValidationError(
                    "created_at_from ne peut pas être après created_at_to.",
                    field_name="created_at_from",
                )

        # order_by whitelist (sécurité)
        allowed_order_by = {"id", "created_at", "nom", "prix_achat", "a_ete_achete", "localisation"}
        if data.get("order_by") not in allowed_order_by:
            raise ValidationError(
                f"order_by invalide (autorisés: {', '.join(sorted(allowed_order_by))})",
                field_name="order_by",
            )

class StockCreateSchema(Schema):
    """Payload attendu pour POST /api/stock"""

    nom = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(allow_none=True, load_default=None)
    localisation = fields.Str(allow_none=True, load_default=None)

    a_ete_achete = fields.Bool(load_default=False)

    # modèle: Float nullable
    prix_achat = fields.Float(allow_none=True, load_default=None)

    # modèle: DateTime nullable
    # Tu peux laisser le backend définir created_at si absent.
    created_at = fields.DateTime(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_create(self, data, **kwargs):
        # prix >= 0
        if data.get("prix_achat") is not None and data["prix_achat"] < 0:
            raise ValidationError("prix_achat ne peut pas être négatif.", field_name="prix_achat")


class StockDeleteResponseSchema(Schema):
    """Réponse JSON si tu renvoies 200 au lieu de 204."""
    ok = fields.Bool(dump_only=True)
    deleted_stock_id = fields.Int(dump_only=True)

class StockUpdateSchema(Schema):
    """
    Payload PATCH /api/stock/<id>
    Tous les champs sont optionnels.
    """

    nom = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    localisation = fields.Str(allow_none=True)

    a_ete_achete = fields.Bool(allow_none=True)

    # modèle: Float nullable
    prix_achat = fields.Float(allow_none=True)

    # DateTime nullable
    created_at = fields.DateTime(allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_patch(self, data, **kwargs):
        if not data:
            raise ValidationError("Aucun champ fourni pour la mise à jour.")

        if data.get("prix_achat") is not None and data["prix_achat"] < 0:
            raise ValidationError(
                "prix_achat ne peut pas être négatif.",
                field_name="prix_achat",
            )