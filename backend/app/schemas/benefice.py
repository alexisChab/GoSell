from marshmallow import Schema, fields, validate, EXCLUDE


class BenefitFilterSchema(Schema):
    """
    Query params pour GET /benefices
    """
    include_products = fields.Bool(load_default=True)
    include_stocks = fields.Bool(load_default=True)
    include_fees = fields.Bool(load_default=True)

    # ---- filtres produits ----
    products_en_vente = fields.Bool(allow_none=True, load_default=None)
    products_est_vendu = fields.Bool(allow_none=True, load_default=None)
    products_a_ete_achete = fields.Bool(allow_none=True, load_default=None)

    products_prix_achat_min = fields.Float(allow_none=True, load_default=None)
    products_prix_achat_max = fields.Float(allow_none=True, load_default=None)

    # liste IDs via "1,2,3"
    product_ids = fields.Str(allow_none=True, load_default=None)

    # exclure les produits qui sont dans un lot
    exclude_lot_products = fields.Bool(load_default=False)

    # ---- filtres stocks ----
    stocks_a_ete_achete = fields.Bool(allow_none=True, load_default=None)

    stocks_prix_achat_min = fields.Float(allow_none=True, load_default=None)
    stocks_prix_achat_max = fields.Float(allow_none=True, load_default=None)

    stock_ids = fields.Str(allow_none=True, load_default=None)

    # ---- filtres taxonomie ----
    # (produits sûr ; stocks seulement si relation existe)
    categorie_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    genre_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    type_produit_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))

    class Meta:
        unknown = EXCLUDE


class BenefitCountsSchema(Schema):
    nb_produits = fields.Int(dump_only=True)
    nb_stocks = fields.Int(dump_only=True)
    nb_produits_ignored_missing_expected = fields.Int(dump_only=True)
    nb_produits_ignored_missing_cost = fields.Int(dump_only=True)


class BenefitTotalsSchema(Schema):
    # coûts
    cost_products = fields.Float(dump_only=True)
    cost_stocks = fields.Float(dump_only=True)
    fees = fields.Float(dump_only=True)
    cost_total = fields.Float(dump_only=True)

    # “revenu attendu” médian (produits uniquement)
    revenue_expected_median = fields.Float(dump_only=True)

    # bénéfice attendu (médian)
    profit_expected_median = fields.Float(dump_only=True)
    is_profit_expected_median = fields.Bool(dump_only=True)


class BenefitScopeSchema(Schema):
    include_products = fields.Bool(dump_only=True)
    include_stocks = fields.Bool(dump_only=True)
    include_fees = fields.Bool(dump_only=True)


class BenefitSummaryReadSchema(Schema):
    scope = fields.Nested(BenefitScopeSchema, dump_only=True)
    counts = fields.Nested(BenefitCountsSchema, dump_only=True)
    totals = fields.Nested(BenefitTotalsSchema, dump_only=True)

class ProductWhatIfQuerySchema(Schema):
    """
    Query params:
      /products/<id>/whatif?offer_price=30
    """
    offer_price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        unknown = EXCLUDE


class ProductForecastQuerySchema(Schema):
    """
    Query params:
      /products/<id>/forecast
      /products/<id>/forecast?offer_price=30
      /products/<id>/forecast?haircut_percent=20
      /products/<id>/forecast?offer_price=30&haircut_percent=20
    """
    offer_price = fields.Float(allow_none=True, load_default=None, validate=validate.Range(min=0))
    haircut_percent = fields.Float(allow_none=True, load_default=None, validate=validate.Range(min=0, max=100))

    class Meta:
        unknown = EXCLUDE


# -----------------------------
# Outputs
# -----------------------------

class ProfitKpiSchema(Schema):
    """
    KPI unique basé sur le coût_total:
      multiple = price / cost_total
    """
    price = fields.Float(dump_only=True, allow_none=True)          # prix de vente simulé (scenario)
    cost_total = fields.Float(dump_only=True, allow_none=True)     # coût total (achat + frais)
    profit_amount = fields.Float(dump_only=True, allow_none=True)  # price - cost_total
    multiple = fields.Float(dump_only=True, allow_none=True)       # price / cost_total (None si cost_total==0)
    is_profit = fields.Bool(dump_only=True, allow_none=True)       # profit_amount > 0


class ProductWhatIfReadSchema(Schema):
    """
    Réponse:
      GET /products/<id>/whatif?offer_price=...
    """
    product_id = fields.Int(dump_only=True)

    from_lot = fields.Bool(dump_only=True)
    a_ete_achete = fields.Bool(dump_only=True)

    offer = fields.Nested(ProfitKpiSchema, dump_only=True)

    # Pour debug / UI
    reason = fields.Str(
        dump_only=True,
        allow_none=True,
        validate=validate.OneOf([
            "CALCUL_AU_NIVEAU_DU_LOT",
            "PRIX_ACHAT_MANQUANT",
            "PRIX_ESPERES_INSUFFISANTS",
            "ZERO_COST",  # cost_total == 0 => multiple infini/indéfini
        ]),
    )


class ProductForecastScenariosSchema(Schema):
    """
    Scénarios forecast: min / median / max (+ offer optionnel)
    """
    min = fields.Nested(ProfitKpiSchema, dump_only=True)
    median = fields.Nested(ProfitKpiSchema, dump_only=True)
    max = fields.Nested(ProfitKpiSchema, dump_only=True)

    # optionnel si offer_price présent
    offer = fields.Nested(ProfitKpiSchema, dump_only=True, allow_none=True)


class ProductForecastReadSchema(Schema):
    """
    Réponse:
      GET /products/<id>/forecast
    """
    product_id = fields.Int(dump_only=True)

    from_lot = fields.Bool(dump_only=True)
    a_ete_achete = fields.Bool(dump_only=True)

    # rappel du haircut appliqué
    haircut_percent = fields.Float(dump_only=True, allow_none=True)

    # coûts calculés une seule fois (pour éviter redondance)
    cost_total = fields.Float(dump_only=True, allow_none=True)

    scenarios = fields.Nested(ProductForecastScenariosSchema, dump_only=True)

    reason = fields.Str(
        dump_only=True,
        allow_none=True,
        validate=validate.OneOf([
            "CALCUL_AU_NIVEAU_DU_LOT",
            "PRIX_ACHAT_MANQUANT",
            "PRIX_ESPERES_INSUFFISANTS",
            "ZERO_COST",
        ]),
    )

class RiskProductsQuerySchema(Schema):
    # filtres utiles
    limit = fields.Int(load_default=50, validate=validate.Range(min=1, max=500))
    only_en_vente = fields.Bool(load_default=True)
    include_lot_products = fields.Bool(load_default=False)  # si False -> on exclut ceux en lot
    threshold_multiple = fields.Float(load_default=1.0, validate=validate.Range(min=0))

    # filtres taxonomie (produits)
    categorie_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    genre_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    type_produit_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))

    class Meta:
        unknown = EXCLUDE


class RiskProductItemSchema(Schema):
    product_id = fields.Int(dump_only=True)
    nom = fields.Str(dump_only=True, allow_none=True)

    from_lot = fields.Bool(dump_only=True)

    median_expected = fields.Float(dump_only=True, allow_none=True)
    cost_total = fields.Float(dump_only=True, allow_none=True)

    profit_amount = fields.Float(dump_only=True, allow_none=True)
    multiple = fields.Float(dump_only=True, allow_none=True)

    risk_level = fields.Str(
        dump_only=True,
        validate=validate.OneOf(["LOSS", "LOW_MARGIN"])
    )

    reason = fields.Str(
        dump_only=True,
        allow_none=True,
        validate=validate.OneOf([
            "CALCUL_AU_NIVEAU_DU_LOT",
            "PRIX_ESPERES_INSUFFISANTS",
            "PRIX_ACHAT_MANQUANT",
            "ZERO_COST",
        ]),
    )


class RiskProductsReadSchema(Schema):
    items = fields.Nested(RiskProductItemSchema, many=True, dump_only=True)
    count = fields.Int(dump_only=True)

class BestTypesQuerySchema(Schema):
    min_multiple = fields.Float(load_default=1.5, validate=validate.Range(min=0))
    min_count = fields.Int(load_default=3, validate=validate.Range(min=1, max=1000))
    only_en_vente = fields.Bool(load_default=True)
    exclude_lot_products = fields.Bool(load_default=True)

    # “pas trop cher”
    max_avg_cost_total = fields.Float(allow_none=True, load_default=None, validate=validate.Range(min=0))

    # taxonomie optionnelle
    categorie_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    genre_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))

    limit = fields.Int(load_default=50, validate=validate.Range(min=1, max=500))

    class Meta:
        unknown = EXCLUDE


class BestTypeItemSchema(Schema):
    type_produit_id = fields.Int(dump_only=True)
    type_produit_nom = fields.Str(dump_only=True, allow_none=True)

    count_products = fields.Int(dump_only=True)
    count_profitable = fields.Int(dump_only=True)
    success_rate = fields.Float(dump_only=True)

    avg_multiple_median = fields.Float(dump_only=True)
    avg_cost_total = fields.Float(dump_only=True)
    avg_profit_amount = fields.Float(dump_only=True)


class BestTypesReadSchema(Schema):
    filters = fields.Dict(dump_only=True)
    items = fields.Nested(BestTypeItemSchema, many=True, dump_only=True)
    count = fields.Int(dump_only=True)

class BenefitBreakdownQuerySchema(Schema):
    # categorie | genre | type_produit
    group_by = fields.Str(
        required=True,
        validate=validate.OneOf(["categorie", "genre", "type_produit"])
    )

    include_fees = fields.Bool(load_default=True)
    exclude_lot_products = fields.Bool(load_default=True)

    only_en_vente = fields.Bool(load_default=False)
    only_unsold = fields.Bool(load_default=False)  # si True => est_vendu=False

    min_count = fields.Int(load_default=1, validate=validate.Range(min=1, max=1000))
    limit = fields.Int(load_default=50, validate=validate.Range(min=1, max=500))

    class Meta:
        unknown = EXCLUDE


class BenefitBreakdownItemSchema(Schema):
    group_id = fields.Int(dump_only=True, allow_none=True)
    group_name = fields.Str(dump_only=True, allow_none=True)

    count_products = fields.Int(dump_only=True)

    revenue_expected_median = fields.Float(dump_only=True)
    cost_products = fields.Float(dump_only=True)
    fees = fields.Float(dump_only=True)
    cost_total = fields.Float(dump_only=True)

    profit_expected_median = fields.Float(dump_only=True)
    is_profit_expected_median = fields.Bool(dump_only=True)

    avg_multiple_median = fields.Float(dump_only=True, allow_none=True)  # revenue / cost_total si cost_total>0


class BenefitBreakdownReadSchema(Schema):
    group_by = fields.Str(dump_only=True)
    items = fields.Nested(BenefitBreakdownItemSchema, many=True, dump_only=True)
    count = fields.Int(dump_only=True)