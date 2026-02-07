from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.schemas.stock import StockReadSchema, StockFilterSchema
from app.crud.stock import get_stock_for_user

stock_bp = Blueprint("stock", __name__, url_prefix="/api")

_stock_out = StockReadSchema(many=True)
_filters_in = StockFilterSchema()


@stock_bp.get("/stock")
@jwt_required()
def get_stock():
    user_id = int(get_jwt_identity())

    raw = request.args.to_dict(flat=True)

    try:
        filters = _filters_in.load(raw)
    except ValidationError as e:
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "messages": e.messages,
            }
        }, 400

    items = get_stock_for_user(user_id, filters)
    return jsonify(_stock_out.dump(items)), 200
