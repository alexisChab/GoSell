from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.schemas.stock import StockReadSchema, StockFilterSchema, StockCreateSchema, StockUpdateSchema
from app.crud.stock import get_stock_for_user, create_stock_item, delete_stock_item, NotFoundError, update_stock_item

stock_bp = Blueprint("stock", __name__, url_prefix="/api")

_stock_out = StockReadSchema(many=True)
_filters_in = StockFilterSchema()
_stock_in = StockCreateSchema()
_stock_out_one = StockReadSchema()
_patch_in = StockUpdateSchema()

@stock_bp.get("/stock")
@jwt_required()
def get_stock():
    user_id = int(get_jwt_identity())

    raw = request.args.to_dict(flat=True)

    try:
        filters = _filters_in.load(raw)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    items = get_stock_for_user(user_id, filters)
    return jsonify(_stock_out.dump(items)), 200

@stock_bp.post("/stock")
@jwt_required()
def post_stock():
    user_id = int(get_jwt_identity())

    try:
        data = _stock_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    item = create_stock_item(user_id, data)
    return jsonify(_stock_out_one.dump(item)), 201


@stock_bp.delete("/stock/<int:stock_id>")
@jwt_required()
def delete_stock(stock_id: int):
    user_id = int(get_jwt_identity())

    try:
        delete_stock_item(user_id, stock_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Stock introuvable"}}, 404

    # Option REST: return "", 204
    return {"ok": True, "deleted_stock_id": stock_id}, 200

@stock_bp.patch("/stock/<int:stock_id>")
@jwt_required()
def patch_stock(stock_id: int):
    user_id = int(get_jwt_identity())

    try:
        patch_data = _patch_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    try:
        item = update_stock_item(user_id, stock_id, patch_data)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Stock introuvable"}}, 404

    return jsonify(_stock_out_one.dump(item)), 200






