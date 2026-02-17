from marshmallow import Schema, fields, validate, EXCLUDE, validates_schema, ValidationError
from app.schemas.stock import StockReadSchema
class ProductReadSchema(Schema):
    """Réponse GET produit."""
    id = fields.Int(dump_only=True)

    nom = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True, allow_none=True)

    en_vente = fields.Bool(dump_only=True)
    est_vendu = fields.Bool(dump_only=True)
    a_ete_achete = fields.Bool(dump_only=True)

    prix_achat = fields.Float(dump_only=True, allow_none=True)
    prix_vente = fields.Float(dump_only=True, allow_none=True)
    prix_min_espere = fields.Float(dump_only=True, allow_none=True)
    prix_max_espere = fields.Float(dump_only=True, allow_none=True)

    date_mise_en_vente = fields.Date(dump_only=True, allow_none=True)

    user_id = fields.Int(dump_only=True)

class ProductCreateSchema(Schema):
    """Payload attendu pour POST /products"""

    nom = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(allow_none=True, load_default=None)

    en_vente = fields.Bool(load_default=False)
    est_vendu = fields.Bool(load_default=False)
    a_ete_achete = fields.Bool(load_default=False)

    prix_achat = fields.Float(allow_none=True, load_default=0)
    prix_vente = fields.Float(allow_none=True, load_default=None)
    prix_min_espere = fields.Float(allow_none=True, load_default=0)
    prix_max_espere = fields.Float(allow_none=True, load_default=0)

    date_mise_en_vente = fields.Date(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_prices(self, data, **kwargs):
        # Exemples de validations simples “métier”
        for k in ("prix_achat", "prix_vente", "prix_min_espere", "prix_max_espere"):
            if k in data and data[k] is not None and data[k] < 0:
                raise ValidationError("Un prix ne peut pas être négatif.", field_name=k)

        # Si tu veux : min <= max
        if data.get("prix_min_espere") is not None and data.get("prix_max_espere") is not None:
            if data["prix_min_espere"] > data["prix_max_espere"]:
                raise ValidationError("prix_min_espere ne peut pas être > prix_max_espere.",
                                      field_name="prix_min_espere")


class ProductPatchSchema(Schema):
    """Payload PATCH /products/<id> : update partiel"""

    nom = fields.Str(validate=validate.Length(min=1))
    description = fields.Str(allow_none=True)

    en_vente = fields.Bool()
    est_vendu = fields.Bool()
    a_ete_achete = fields.Bool()

    prix_achat = fields.Float(allow_none=True)
    prix_vente = fields.Float(allow_none=True)
    prix_min_espere = fields.Float(allow_none=True)
    prix_max_espere = fields.Float(allow_none=True)

    date_mise_en_vente = fields.Date(allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_patch(self, data, **kwargs):
        # PATCH vide = pas utile
        if not data:
            raise ValidationError("Aucun champ à modifier.")

        # prix >= 0
        for k in ("prix_achat", "prix_vente", "prix_min_espere", "prix_max_espere"):
            if k in data and data[k] is not None and data[k] < 0:
                raise ValidationError("Un prix ne peut pas être négatif.", field_name=k)

        # min <= max (si les deux sont présents dans le PATCH)
        if "prix_min_espere" in data and "prix_max_espere" in data:
            if data["prix_min_espere"] is not None and data["prix_max_espere"] is not None:
                if data["prix_min_espere"] > data["prix_max_espere"]:
                    raise ValidationError(
                        "prix_min_espere ne peut pas être > prix_max_espere.",
                        field_name="prix_min_espere",
                    )

class ProductDeleteParamsSchema(Schema):
    """
    Optionnel : utile si tu veux valider l'id venant de l'URL
    (sinon tu le fais au niveau du route param <int:product_id>).
    """
    product_id = fields.Int(required=True, validate=validate.Range(min=1))


class ProductDeleteResponseSchema(Schema):
    """Réponse JSON si tu renvoies 200 au lieu de 204."""
    ok = fields.Bool(dump_only=True)
    deleted_product_id = fields.Int(dump_only=True)
    message = fields.Str(dump_only=True)

class ProductToStockRequestSchema(Schema):
    """
    Payload pour une route du style:
      POST /products/<id>/to-stock
    """
    note = fields.Str(allow_none=True)
    date_entree_stock = fields.Date(allow_none=True)

    valeur_estimee = fields.Float(allow_none=True)

    raison = fields.Str(allow_none=True)

    stop_sale = fields.Bool(load_default=True)

    class Meta:
        unknown = EXCLUDE

class ProductToStockResponseSchema(Schema):
    """
    Réponse de la route produit->stock :
    - confirme la suppression côté produit
    - renvoie l'objet stock créé
    """
    ok = fields.Bool(dump_only=True)
    moved_product_id = fields.Int(dump_only=True)
    stock_item = fields.Nested(StockReadSchema, dump_only=True)
    message = fields.Str(dump_only=True)

class ProductFilterSchema(Schema):
    """
    Schéma de filtrage pour GET /products
    """


    search = fields.Str(allow_none=True)

    prix_achat_min = fields.Float(allow_none=True)
    prix_achat_max = fields.Float(allow_none=True)

    prix_vente_min = fields.Float(allow_none=True)
    prix_vente_max = fields.Float(allow_none=True)

    prix_min_espere_min = fields.Float(allow_none=True)
    prix_min_espere_max = fields.Float(allow_none=True)

    prix_max_espere_min = fields.Float(allow_none=True)
    prix_max_espere_max = fields.Float(allow_none=True)

    en_vente = fields.Bool(allow_none=True)
    est_vendu = fields.Bool(allow_none=True)
    a_ete_achete = fields.Bool(allow_none=True)

    date_mise_en_vente_from = fields.Date(allow_none=True)
    date_mise_en_vente_to = fields.Date(allow_none=True)

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))

    order_by = fields.Str(
        validate=validate.OneOf([
            "date_mise_en_vente",
            "prix_vente",
            "prix_achat",
            "nom"
        ]),
        allow_none=True
    )
    order_dir = fields.Str(
        validate=validate.OneOf(["asc", "desc"]),
        load_default="desc"
    )

    class Meta:
        unknown = EXCLUDE


class ProductFinancePrixSchema(Schema):
    min_espere = fields.Float(dump_only=True, allow_none=True)
    max_espere = fields.Float(dump_only=True, allow_none=True)
    median_espere = fields.Float(dump_only=True, allow_none=True)


class ProductFinanceFeesSchema(Schema):
    delivery_fees = fields.Float(dump_only=True)
    other_fees = fields.Float(dump_only=True)
    total_fees = fields.Float(dump_only=True)


class ProductFinanceCostsSchema(Schema):
    # coût achat : peut être None si from_lot=True
    cout_achat = fields.Float(dump_only=True, allow_none=True)

    # cout_total : cout_achat + frais (peut être None si from_lot=True
    # ou si données insuffisantes)
    cout_total = fields.Float(dump_only=True, allow_none=True)

    # optionnel mais très utile côté front pour afficher "GRATUIT" / "PRODUIT_PRIX_ACHAT"
    cost_source = fields.Str(
        dump_only=True,
        allow_none=True,
        validate=validate.OneOf(["GRATUIT", "PRODUIT_PRIX_ACHAT"])
    )


class ProductFinanceProfitSchema(Schema):
    # bénéfice espéré basé sur le prix médian espéré
    benefice_espere = fields.Float(dump_only=True, allow_none=True)

    # booléen direct pour le front
    is_benefice_espere = fields.Bool(dump_only=True, allow_none=True)

    # reason pour debug / UI (lot, prix espérés manquants, prix achat manquant)
    reason = fields.Str(
        dump_only=True,
        allow_none=True,
        validate=validate.OneOf([
            "CALCUL_AU_NIVEAU_DU_LOT",
            "PRIX_ESPERES_INSUFFISANTS",
            "PRIX_ACHAT_MANQUANT",
        ]),
    )


class ProductFinanceReadSchema(Schema):
    """
    Réponse GET /products/<id>/finance
    """
    produit_id = fields.Int(dump_only=True)

    # règles métier
    from_lot = fields.Bool(dump_only=True)
    a_ete_achete = fields.Bool(dump_only=True)

    prix = fields.Nested(ProductFinancePrixSchema, dump_only=True)
    fees = fields.Nested(ProductFinanceFeesSchema, dump_only=True)
    costs = fields.Nested(ProductFinanceCostsSchema, dump_only=True)
    profit = fields.Nested(ProductFinanceProfitSchema, dump_only=True)