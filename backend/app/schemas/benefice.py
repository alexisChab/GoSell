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