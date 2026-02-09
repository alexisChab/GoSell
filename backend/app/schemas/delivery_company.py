from marshmallow import Schema, fields


class DeliveryCompanyReadSchema(Schema):
    id = fields.Int(dump_only=True)
    nom = fields.Str(dump_only=True)
class DeliveryCompanyCreateSchema(Schema):
    nom = fields.Str(required=True)
class DeliveryCompanyPatchSchema(Schema):
    nom = fields.Str(required=False)
class DeliveryCompanyDeleteSchema(Schema):
    id = fields.Int(required=True)
