from marshmallow import Schema, fields, validate, EXCLUDE, validates_schema, ValidationError

class StockReadSchema(Schema):
    """
    Schéma de lecture d'un item du stock.
    """

    id = fields.Int(dump_only=True)

    nom = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)

    # Valeurs financières
    prix_achat = fields.Float(dump_only=True, allow_none=True)
    valeur_estimee = fields.Float(dump_only=True, allow_none=True)

    created_at = fields.Date(dump_only=True, allow_none=True)

    # Ownership
    user_id = fields.Int(dump_only=True)

    class Meta:
        unknown = EXCLUDE

class StockFilterSchema(Schema):
    """
    Query params pour GET /api/stock
    """

    search = fields.Str(load_default=None)

    # ranges
    prix_achat_min = fields.Float(allow_none=True, load_default=None)
    prix_achat_max = fields.Float(allow_none=True, load_default=None)

    valeur_estimee_min = fields.Float(allow_none=True, load_default=None)
    valeur_estimee_max = fields.Float(allow_none=True, load_default=None)

    # dates
    created_at = fields.Date(allow_none=True, load_default=None)

    # tri + pagination
    order_by = fields.Str(load_default="date_entree_stock")
    order_dir = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=200))

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_filters(self, data, **kwargs):
        # --------
        # valeurs >= 0
        # --------
        for k in (
            "prix_achat_min",
            "prix_achat_max",
            "valeur_estimee_min",
            "valeur_estimee_max",
        ):
            if data.get(k) is not None and data[k] < 0:
                raise ValidationError("La valeur ne peut pas être négative.", field_name=k)

        # --------
        # min <= max
        # --------
        if data.get("prix_achat_min") is not None and data.get("prix_achat_max") is not None:
            if data["prix_achat_min"] > data["prix_achat_max"]:
                raise ValidationError(
                    "prix_achat_min ne peut pas être > prix_achat_max.",
                    field_name="prix_achat_min",
                )

        if data.get("valeur_estimee_min") is not None and data.get("valeur_estimee_max") is not None:
            if data["valeur_estimee_min"] > data["valeur_estimee_max"]:
                raise ValidationError(
                    "valeur_estimee_min ne peut pas être > valeur_estimee_max.",
                    field_name="valeur_estimee_min",
                )

        # --------
        # dates from <= to
        # --------
        if data.get("date_entree_from") is not None and data.get("date_entree_to") is not None:
            if data["date_entree_from"] > data["date_entree_to"]:
                raise ValidationError(
                    "date_entree_from ne peut pas être après date_entree_to.",
                    field_name="date_entree_from",
                )

        # --------
        # order_by whitelist (SECURITE)
        # --------
        allowed_order_by = {
            "id",
            "date_entree_stock",
            "nom",
            "prix_achat",
            "valeur_estimee",
        }

        if data.get("order_by") not in allowed_order_by:
            raise ValidationError(
                f"order_by invalide (autorisés: {', '.join(sorted(allowed_order_by))})",
                field_name="order_by",
            )