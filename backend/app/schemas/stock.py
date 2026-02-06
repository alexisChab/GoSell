from marshmallow import Schema, fields, validate, EXCLUDE

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

    # Métadonnées stock
    note = fields.Str(dump_only=True, allow_none=True)
    date_entree_stock = fields.Date(dump_only=True, allow_none=True)

    # Ownership
    user_id = fields.Int(dump_only=True)

    class Meta:
        unknown = EXCLUDE