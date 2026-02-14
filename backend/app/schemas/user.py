# app/schemas/user.py
from marshmallow import Schema, fields, validate


class UserMeSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    username = fields.Str(allow_none=True)
    email = fields.Email(required=True)
    pro = fields.Bool(required=True)


class UserPatchMeSchema(Schema):
    # PATCH: tout optionnel
    name = fields.Str(required=False)
    username = fields.Str(required=False, allow_none=True)
    email = fields.Email(required=False)
    pro = fields.Bool(required=False)


class UserPatchPasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True)
