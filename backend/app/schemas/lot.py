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

class LotFinanceCountsSchema(Schema):
    nb_produits = fields.Int(dump_only=True)
    nb_vendus = fields.Int(dump_only=True)


class LotFinanceRevenueSchema(Schema):
    # CA déjà réalisé (somme des prix_vente des produits vendus du lot)
    revenue_vendu = fields.Float(dump_only=True)

    # Somme des prix médians espérés (min/max) des produits du lot
    revenue_espere_median = fields.Float(dump_only=True, allow_none=True)


class LotFinanceFeesSchema(Schema):
    # frais rattachés au lot (ex: essence, péage, etc.)
    lot_other_fees = fields.Float(dump_only=True)

    # frais rattachés aux produits du lot (livraisons + other_charges produit)
    produits_fees = fields.Float(dump_only=True)

    total_fees = fields.Float(dump_only=True)


class LotFinanceCostsSchema(Schema):
    # prix_total_achat du lot
    achat_lot = fields.Float(dump_only=True)

    # achat_lot + total_fees
    total_cost = fields.Float(dump_only=True)


class LotFinanceProfitSchema(Schema):
    # Profit “attendu” si tout se vend au prix médian espéré
    profit_espere_median = fields.Float(dump_only=True, allow_none=True)

    # bool prêt pour l’UI
    is_profit_espere_median = fields.Bool(dump_only=True, allow_none=True)

    # statut utile quand il manque des infos (ex: prix espérés manquants sur trop de produits)
    reason = fields.Str(
        dump_only=True,
        allow_none=True,
        validate=validate.OneOf([
            "LOT_NOT_FOUND",
            "PRIX_ESPERES_INSUFFISANTS",
        ]),
    )


class LotFinanceReadSchema(Schema):
    """
    Réponse GET /lots/<id>/finance
    """
    lot_id = fields.Int(dump_only=True)

    counts = fields.Nested(LotFinanceCountsSchema, dump_only=True)
    revenue = fields.Nested(LotFinanceRevenueSchema, dump_only=True)
    fees = fields.Nested(LotFinanceFeesSchema, dump_only=True)
    costs = fields.Nested(LotFinanceCostsSchema, dump_only=True)
    profit = fields.Nested(LotFinanceProfitSchema, dump_only=True)