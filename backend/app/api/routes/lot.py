from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.crud.lot import (
    get_lots_by_user,
    get_lot_by_id_for_user,
    create_lot_for_user,
    patch_lot_for_user,
    delete_lot_for_user,
    get_lot_finance_for_user
)

from app.schemas.lot import (
    LotReadSchema,
    LotCreateSchema,
    LotPatchSchema,
    LotFilterSchema,
    LotFinanceReadSchema
)

lot_bp = Blueprint("lot", __name__)

_out_one = LotReadSchema()
_out_many = LotReadSchema(many=True)
_out_finance = LotFinanceReadSchema()
_in_create = LotCreateSchema()
_in_patch = LotPatchSchema()
_in_filters = LotFilterSchema()

@lot_bp.get("/lots")
@jwt_required()
def list_lots_route():
    user_id = get_jwt_identity()

    raw_filters = request.args.to_dict(flat=True)
    filters = _in_filters.load(raw_filters)

    items = get_lots_by_user(user_id=user_id, filters=filters)

    return jsonify(_out_many.dump(items)), 200


@lot_bp.get("/lots/<int:lot_id>")
@jwt_required()
def get_lot_route(lot_id: int):
    user_id = get_jwt_identity()

    item = get_lot_by_id_for_user(user_id=user_id, lot_id=lot_id)

    if item is None:
        return jsonify({"ok": False, "error": "LOT_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200

@lot_bp.post("/lots")
@jwt_required()
def post_lot_route():
    user_id = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_create.load(payload)

    try:
        item = create_lot_for_user(
            user_id=user_id,
            titre=data.get("titre"),
            description=data.get("description"),
            prix_total_achat=data["prix_total_achat"],
            date_achat=data.get("date_achat"),
        )
    except IntegrityError:
        return jsonify({"ok": False, "error": "LOT_CONSTRAINT"}), 409

    return jsonify(_out_one.dump(item)), 201


@lot_bp.patch("/lots/<int:lot_id>")
@jwt_required()
def patch_lot_route(lot_id: int):
    user_id = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_patch.load(payload)

    if not data:
        return jsonify({"ok": False, "error": "NO_FIELDS_TO_PATCH"}), 400

    try:
        item = patch_lot_for_user(
            user_id=user_id,
            lot_id=lot_id,
            data=data,
        )
    except IntegrityError:
        return jsonify({"ok": False, "error": "LOT_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "LOT_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200

@lot_bp.delete("/lots/<int:lot_id>")
@jwt_required()
def delete_lot_route(lot_id: int):
    user_id = get_jwt_identity()

    try:
        ok = delete_lot_for_user(user_id=user_id, lot_id=lot_id)
    except IntegrityError:
        return jsonify({"ok": False, "error": "LOT_CONSTRAINT"}), 409

    if not ok:
        return jsonify({"ok": False, "error": "LOT_NOT_FOUND"}), 404

    return jsonify({"ok": True, "deleted_id": lot_id}), 200

@lot_bp.get("/lots/<int:lot_id>/finance")
@jwt_required()
def get_lot_finance_route(lot_id: int):
    user_id = get_jwt_identity()

    data = get_lot_finance_for_user(user_id=user_id, lot_id=lot_id)

    if data is None:
        return jsonify({"ok": False, "error": "LOT_NOT_FOUND"}), 404

    return jsonify(_out_finance.dump(data)), 200

