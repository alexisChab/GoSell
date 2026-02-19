from marshmallow import Schema, fields, validate


class DashboardCountsSchema(Schema):
    nb_produits_total = fields.Int(dump_only=True)
    nb_produits_en_vente = fields.Int(dump_only=True)
    nb_produits_vendus = fields.Int(dump_only=True)

    nb_lots = fields.Int(dump_only=True)
    nb_stocks = fields.Int(dump_only=True)


class DashboardBenefitSchema(Schema):
    # on ré-embarque la structure de /benefices (sans redéfinir tout)
    scope = fields.Dict(dump_only=True)
    counts = fields.Dict(dump_only=True)
    totals = fields.Dict(dump_only=True)


class DashboardRiskSchema(Schema):
    # on reprend la forme de /risk-products
    items = fields.List(fields.Dict(), dump_only=True)
    count = fields.Int(dump_only=True)


class DashboardBestTypesSchema(Schema):
    # on reprend la forme de /best-types
    filters = fields.Dict(dump_only=True)
    items = fields.List(fields.Dict(), dump_only=True)
    count = fields.Int(dump_only=True)


class DashboardSummaryReadSchema(Schema):
    counts = fields.Nested(DashboardCountsSchema, dump_only=True)

    benefices = fields.Nested(DashboardBenefitSchema, dump_only=True)

    risk_products = fields.Nested(DashboardRiskSchema, dump_only=True)
    best_types = fields.Nested(DashboardBestTypesSchema, dump_only=True)