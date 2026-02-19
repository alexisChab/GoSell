from marshmallow import Schema, fields, validate, EXCLUDE


class CapitalQuerySchema(Schema):
    include_products = fields.Bool(load_default=True)
    include_lots = fields.Bool(load_default=True)
    include_stocks = fields.Bool(load_default=True)

    only_unsold_products = fields.Bool(load_default=True)
    exclude_lot_products = fields.Bool(load_default=True)

    # filtres taxonomie (produits uniquement)
    categorie_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    genre_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))
    type_produit_id = fields.Int(allow_none=True, load_default=None, validate=validate.Range(min=1))

    class Meta:
        unknown = EXCLUDE


class CapitalTotalsSchema(Schema):
    capital_products = fields.Float(dump_only=True)
    capital_lots = fields.Float(dump_only=True)
    capital_stocks = fields.Float(dump_only=True)
    capital_total = fields.Float(dump_only=True)


class CapitalCountsSchema(Schema):
    nb_products_counted = fields.Int(dump_only=True)
    nb_lots_counted = fields.Int(dump_only=True)
    nb_stocks_counted = fields.Int(dump_only=True)


class CapitalReadSchema(Schema):
    scope = fields.Dict(dump_only=True)
    counts = fields.Nested(CapitalCountsSchema, dump_only=True)
    totals = fields.Nested(CapitalTotalsSchema, dump_only=True)