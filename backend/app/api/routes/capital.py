from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas.capital import CapitalQuerySchema, CapitalReadSchema
from app.crud.capital import get_capital_for_user

capital_bp = Blueprint("capital", __name__)

_in = CapitalQuerySchema()
_out = CapitalReadSchema()


@capital_bp.get("/capital")
@jwt_required()
def get_capital():
    user_id = int(get_jwt_identity())

    try:
        raw = request.args.to_dict(flat=True)
        args = _in.load(raw)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    data = get_capital_for_user(user_id=user_id, filters=args)
    return jsonify(_out.dump(data)), 200