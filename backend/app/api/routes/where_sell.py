from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.crud.where_sell import (
    get_where_sells,
    get_where_sell,
    create_where_sell,
    patch_where_sell,
    delete_where_sell,
)

from app.schemas.where_sell import (
    WhereSellReadSchema,
    WhereSellCreateSchema,
    WhereSellPatchSchema,
    WhereSellFilterSchema,
)

where_sell_bp = Blueprint("where_sell", __name__)

_out_one = WhereSellReadSchema()
_out_many = WhereSellReadSchema(many=True)

_in_create = WhereSellCreateSchema()
_in_patch = WhereSellPatchSchema()
_in_filters = WhereSellFilterSchema()


@where_sell_bp.get("/ou-ventes")
@jwt_required()
def list_where_sells_route():
    _ = get_jwt_identity()

    raw = request.args.to_dict(flat=True)
    filters = _in_filters.load(raw)

    items = get_where_sells(filters)
    return jsonify(_out_many.dump(items)), 200


@where_sell_bp.get("/ou-ventes/<int:produit_id>/<int:plateforme_id>")
@jwt_required()
def get_where_sell_route(produit_id: int, plateforme_id: int):
    _ = get_jwt_identity()

    item = get_where_sell(produit_id, plateforme_id)
    if item is None:
        return jsonify({"ok": False, "error": "OU_VENTE_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200


@where_sell_bp.post("/ou-ventes")
@jwt_required()
def post_where_sell_route():
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_create.load(payload)

    try:
        item = create_where_sell(
            produit_id=data["produit_id"],
            plateforme_id=data["plateforme_id"],
            lien=data.get("lien"),
        )
    except IntegrityError:
        # - doublon PK composite (déjà existant)
        # - FK produit_id invalide
        # - FK plateforme_id invalide
        return jsonify({"ok": False, "error": "OU_VENTE_CONSTRAINT"}), 409

    return jsonify(_out_one.dump(item)), 201


@where_sell_bp.patch("/ou-ventes/<int:produit_id>/<int:plateforme_id>")
@jwt_required()
def patch_where_sell_route(produit_id: int, plateforme_id: int):
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _in_patch.load(payload)

    try:
        item = patch_where_sell(produit_id, plateforme_id, data)
    except IntegrityError:
        return jsonify({"ok": False, "error": "OU_VENTE_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "OU_VENTE_NOT_FOUND"}), 404

    return jsonify(_out_one.dump(item)), 200


@where_sell_bp.delete("/ou-ventes/<int:produit_id>/<int:plateforme_id>")
@jwt_required()
def delete_where_sell_route(produit_id: int, plateforme_id: int):
    _ = get_jwt_identity()

    ok = delete_where_sell(produit_id, plateforme_id)
    if not ok:
        return jsonify({"ok": False, "error": "OU_VENTE_NOT_FOUND"}), 404

    return jsonify(
        {"ok": True, "deleted": {"produit_id": produit_id, "plateforme_id": plateforme_id}}
    ), 200

