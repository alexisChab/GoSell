from marshmallow import Schema, fields

class CategoryReadSchema(Schema):
    id = fields.Int(dump_only=True)
    intitule = fields.Str(required=True)

class CategoryCreateSchema(Schema):
    intitule = fields.Str(required=True)

class CategoryPatchSchema(Schema):
    intitule = fields.Str(required=False)

class CategoryDeleteSchema(Schema):
    pass
