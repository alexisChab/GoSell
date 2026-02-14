from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.crud.other_charges import (
    get_other_charges_by_user,
    get_other_charge_by_id_for_user,
    create_other_charge_for_user,
    patch_other_charge_for_user,
    delete_other_charge_for_user,
)

from app.schemas.other_charges import (
    OtherChargesReadSchema,
    OtherChargesCreateSchema,
    OtherChargesPatchSchema,
    OtherChargesFilterSchema,
)

other_charges_bp = Blueprint("other_charges", __name__)

_out_one = OtherChargesReadSchema()
_out_many = OtherChargesReadSchema(many=True)

_in_create = OtherChargesCreateSchema()
_in_patch = OtherChargesPatchSchema()
_in_filters = OtherChargesFilterSchema()

@other_charges_bp.get("/frais-annexes")
@jwt_required()
def list_other_charges_route():
    user_id = get_jwt_identity()

    raw = request.args.to_dict(flat=True)
    filters = _in_filters.load(raw)

    items = get_other_charges_by_user(user_id=user_id, filters=filters)
    return jsonify(_out_many.dump(items)), 200

@other_charges_bp.get("/frais-annexes/<int:charge_id>")
@jwt_required()
def get_other_charge_route(charge_id: int):
    user_id = get_jwt_identity()

    item = get_other_charge_by_id_for_user(user_id=user_id, charge_id=charge_id)
    if item is None:
        return jsonify({"ok": False, "error": "OTHER_CHARGE_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200

@other_charges_bp.post("/frais-annexes")
@jwt_required()
def post_other_charge_route():
    user_id = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_create.load(payload)

    try:
        item = create_other_charge_for_user(
            user_id=user_id,
            intitule=data["intitule"],
            montant=data["montant"],
            lot_id=data.get("lot_id"),
            produit_id=data.get("produit_id"),
        )
    except ValueError:
        return jsonify({"ok": False, "error": "INVALID_TARGET"}), 400
    except IntegrityError:
        return jsonify({"ok": False, "error": "OTHER_CHARGE_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "TARGET_NOT_OWNED"}), 403

    return jsonify(_out_one.dump(item)), 201

@other_charges_bp.patch("/frais-annexes/<int:charge_id>")
@jwt_required()
def patch_other_charge_route(charge_id: int):
    user_id = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_patch.load(payload)

    if not data:
        return jsonify({"ok": False, "error": "NO_FIELDS_TO_PATCH"}), 400

    try:
        item = patch_other_charge_for_user(
            user_id=user_id,
            charge_id=charge_id,
            data=data,
        )
    except ValueError:
        return jsonify({"ok": False, "error": "INVALID_TARGET"}), 400
    except IntegrityError:
        return jsonify({"ok": False, "error": "OTHER_CHARGE_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "OTHER_CHARGE_NOT_FOUND_OR_NOT_OWNED"}), 404

    return jsonify(_out_one.dump(item)), 200

@other_charges_bp.delete("/frais-annexes/<int:charge_id>")
@jwt_required()
def delete_other_charge_route(charge_id: int):
    user_id = get_jwt_identity()

    try:
        ok = delete_other_charge_for_user(user_id=user_id, charge_id=charge_id)
    except IntegrityError:
        return jsonify({"ok": False, "error": "OTHER_CHARGE_CONSTRAINT"}), 409

    if not ok:
        return jsonify({"ok": False, "error": "OTHER_CHARGE_NOT_FOUND"}), 404

    return jsonify({"ok": True, "deleted_id": charge_id}), 200


