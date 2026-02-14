from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.crud.lot_produit import (
    get_lot_produits_by_user,
    get_lot_produit_by_id_for_user,
    create_lot_produit_for_user,
    patch_lot_produit_for_user,
    delete_lot_produit_for_user,
)

from app.schemas.lot_produit import (
    LotProduitReadSchema,
    LotProduitCreateSchema,
    LotProduitPatchSchema,
    LotProduitFilterSchema,
)

lot_produit_bp = Blueprint("lot_produit", __name__)

_out_one = LotProduitReadSchema()
_out_many = LotProduitReadSchema(many=True)

_in_create = LotProduitCreateSchema()
_in_patch = LotProduitPatchSchema()
_in_filters = LotProduitFilterSchema()

@lot_produit_bp.get("/lot-produits")
@jwt_required()
def list_lot_produits_route():
    user_id = get_jwt_identity()

    raw_filters = request.args.to_dict(flat=True)
    filters = _in_filters.load(raw_filters)

    items = get_lot_produits_by_user(user_id=user_id, filters=filters)

    return jsonify(_out_many.dump(items)), 200


@lot_produit_bp.get("/lot-produits/<int:lot_produit_id>")
@jwt_required()
def get_lot_produit_route(lot_produit_id: int):
    user_id = get_jwt_identity()

    item = get_lot_produit_by_id_for_user(
        user_id=user_id,
        lot_produit_id=lot_produit_id,
    )

    if item is None:
        return jsonify({"ok": False, "error": "LOT_PRODUIT_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200


@lot_produit_bp.post("/lot-produits")
@jwt_required()
def post_lot_produit_route():
    user_id = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_create.load(payload)

    try:
        item = create_lot_produit_for_user(
            user_id=user_id,
            lot_id=data["lot_id"],
            produit_id=data["produit_id"],
            quantite=data.get("quantite", 1),
            allocation_prix_achat=data.get("allocation_prix_achat"),
            allocation_frais=data.get("allocation_frais"),
            allocation_methode=data.get("allocation_methode"),
        )
    except IntegrityError:
        return jsonify({"ok": False, "error": "LOT_PRODUIT_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "LOT_NOT_OWNED"}), 403

    return jsonify(_out_one.dump(item)), 201




@lot_produit_bp.patch("/lot-produits/<int:lot_produit_id>")
@jwt_required()
def patch_lot_produit_route(lot_produit_id: int):
    user_id = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_patch.load(payload)

    if not data:
        return jsonify({"ok": False, "error": "NO_FIELDS_TO_PATCH"}), 400

    try:
        item = patch_lot_produit_for_user(
            user_id=user_id,
            lot_produit_id=lot_produit_id,
            data=data,
        )
    except IntegrityError:
        return jsonify({"ok": False, "error": "LOT_PRODUIT_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "LOT_PRODUIT_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200


@lot_produit_bp.delete("/lot-produits/<int:lot_produit_id>")
@jwt_required()
def delete_lot_produit_route(lot_produit_id: int):
    user_id = get_jwt_identity()

    try:
        ok = delete_lot_produit_for_user(
            user_id=user_id,
            lot_produit_id=lot_produit_id,
        )
    except IntegrityError:
        return jsonify({"ok": False, "error": "LOT_PRODUIT_CONSTRAINT"}), 409

    if not ok:
        return jsonify({"ok": False, "error": "LOT_PRODUIT_NOT_FOUND"}), 404

    return jsonify({"ok": True, "deleted_id": lot_produit_id}), 200
