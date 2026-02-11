from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.crud.product_type import (
    get_product_types,
    get_product_type_by_id,
    create_product_type,
    patch_product_type,
    delete_product_type,
)

from app.schemas.product_type import (
    ProductTypeReadSchema,
    ProductTypeCreateSchema,
    ProductTypePatchSchema,
    ProductTypeFilterSchema,
)

product_type_bp = Blueprint("product_type", __name__)

_type_out = ProductTypeReadSchema()
_types_out = ProductTypeReadSchema(many=True)

_type_create_in = ProductTypeCreateSchema()
_type_patch_in = ProductTypePatchSchema()
_type_filters_in = ProductTypeFilterSchema()


@product_type_bp.get("/type-produits")
@jwt_required()
def get_product_types_route():
    _ = get_jwt_identity()
    raw = request.args.to_dict(flat=True)
    filters = _type_filters_in.load(raw)

    items = get_product_types(filters)
    return jsonify(_types_out.dump(items)), 200


@product_type_bp.get("/type-produits/<int:type_id>")
@jwt_required()
def get_product_type_route(type_id: int):
    _ = get_jwt_identity()

    item = get_product_type_by_id(type_id)
    if item is None:
        return jsonify({"ok": False, "error": "TYPE_PRODUIT_NOT_FOUND"}), 404

    return jsonify(_type_out.dump(item)), 200


@product_type_bp.post("/type-produits")
@jwt_required()
def post_product_type_route():
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _type_create_in.load(payload)

    try:
        item = create_product_type(
            nom=data["nom"],
            genre_id=data["genre_id"],
        )
    except IntegrityError:
        # - unique (genre_id, nom)
        # - FK genre_id invalide
        return jsonify({"ok": False, "error": "TYPE_PRODUIT_CONSTRAINT"}), 409

    return jsonify(_type_out.dump(item)), 201


@product_type_bp.patch("/type-produits/<int:type_id>")
@jwt_required()
def patch_product_type_route(type_id: int):
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _type_patch_in.load(payload)

    try:
        item = patch_product_type(type_id, data)
    except IntegrityError:
        return jsonify({"ok": False, "error": "TYPE_PRODUIT_CONSTRAINT"}), 409

    if item is None:
        return jsonify({"ok": False, "error": "TYPE_PRODUIT_NOT_FOUND"}), 404

    return jsonify(_type_out.dump(item)), 200


@product_type_bp.delete("/type-produits/<int:type_id>")
@jwt_required()
def delete_product_type_route(type_id: int):
    _ = get_jwt_identity()

    try:
        ok = delete_product_type(type_id)
    except IntegrityError:
        # typiquement si référencé dans la table pivot produit_type_produit
        return jsonify({"ok": False, "error": "TYPE_PRODUIT_IN_USE"}), 409

    if not ok:
        return jsonify({"ok": False, "error": "TYPE_PRODUIT_NOT_FOUND"}), 404

    return jsonify({"ok": True, "deleted_type_produit_id": type_id}), 200
