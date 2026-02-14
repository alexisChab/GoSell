from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app.crud.delivery_charges import (
    get_delivery_charges,
    get_delivery_charge_by_id,
    create_delivery_charge,
    patch_delivery_charge,
    delete_delivery_charge,
)

from app.schemas.delivery_charges import (
    DeliveryChargesReadSchema,
    DeliveryChargesCreateSchema,
    DeliveryChargesPatchSchema,
    DeliveryChargesFilterSchema,
)

delivery_charges_bp = Blueprint("delivery_charges", __name__)

_out_one = DeliveryChargesReadSchema()
_out_many = DeliveryChargesReadSchema(many=True)

_in_create = DeliveryChargesCreateSchema()
_in_patch = DeliveryChargesPatchSchema()
_in_filters = DeliveryChargesFilterSchema()


# =========================
# GET LIST
# =========================
@delivery_charges_bp.get("/frais-livraison")
@jwt_required()
def list_delivery_charges_route():
    raw = request.args.to_dict(flat=True)
    filters = _in_filters.load(raw)

    items = get_delivery_charges(filters=filters)
    return jsonify(_out_many.dump(items)), 200


# =========================
# GET ONE
# =========================
@delivery_charges_bp.get("/frais-livraison/<int:charge_id>")
@jwt_required()
def get_delivery_charge_route(charge_id: int):
    item = get_delivery_charge_by_id(charge_id)
    if item is None:
        return jsonify({"ok": False, "error": "DELIVERY_CHARGE_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200


# =========================
# POST
# =========================
@delivery_charges_bp.post("/frais-livraison")
@jwt_required()
def post_delivery_charge_route():
    payload = request.get_json(silent=True) or {}
    data = _in_create.load(payload)

    try:
        item = create_delivery_charge(
            montant=data["montant"],
            produit_id=data["produit_id"],
            lot_id=data.get("lot_id"),
            societe_id=data.get("societe_id"),
        )
    except IntegrityError:
        return jsonify({"ok": False, "error": "DELIVERY_CHARGE_CONSTRAINT"}), 409

    return jsonify(_out_one.dump(item)), 201


# =========================
# PATCH
# =========================
@delivery_charges_bp.patch("/frais-livraison/<int:charge_id>")
@jwt_required()
def patch_delivery_charge_route(charge_id: int):
    payload = request.get_json(silent=True) or {}
    data = _in_patch.load(payload)

    if not data:
        return jsonify({"ok": False, "error": "NO_FIELDS_TO_PATCH"}), 400

    try:
        item = patch_delivery_charge(charge_id=charge_id, data=data)
    except IntegrityError:
        return jsonify({"ok": False, "error": "DELIVERY_CHARGE_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "DELIVERY_CHARGE_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200


# =========================
# DELETE
# =========================
@delivery_charges_bp.delete("/frais-livraison/<int:charge_id>")
@jwt_required()
def delete_delivery_charge_route(charge_id: int):
    try:
        ok = delete_delivery_charge(charge_id)
    except IntegrityError:
        return jsonify({"ok": False, "error": "DELIVERY_CHARGE_CONSTRAINT"}), 409

    if not ok:
        return jsonify({"ok": False, "error": "DELIVERY_CHARGE_NOT_FOUND"}), 404

    return jsonify({"ok": True, "deleted_id": charge_id}), 200
