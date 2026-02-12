from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.crud.produit_type_produit import (
    get_produit_type_produits,
    get_produit_type_produit,
    create_produit_type_produit,
    delete_produit_type_produit,
)

from app.schemas.produit_type_produit import (
    ProduitTypeProduitReadSchema,
    ProduitTypeProduitCreateSchema,
    ProduitTypeProduitFilterSchema,
)

produit_type_produit_bp = Blueprint("produit_type_produit", __name__)

_link_out = ProduitTypeProduitReadSchema()
_links_out = ProduitTypeProduitReadSchema(many=True)

_link_create_in = ProduitTypeProduitCreateSchema()
_link_filters_in = ProduitTypeProduitFilterSchema()


@produit_type_produit_bp.get("/produit-type-produits")
@jwt_required()
def list_produit_type_produits_route():
    _ = get_jwt_identity()

    raw = request.args.to_dict(flat=True)
    filters = _link_filters_in.load(raw)

    items = get_produit_type_produits(filters)
    return jsonify(_links_out.dump(items)), 200


@produit_type_produit_bp.get("/produit-type-produits/<int:produit_id>/<int:type_produit_id>")
@jwt_required()
def get_produit_type_produit_route(produit_id: int, type_produit_id: int):
    _ = get_jwt_identity()

    link = get_produit_type_produit(produit_id, type_produit_id)
    if link is None:
        return jsonify({"ok": False, "error": "PRODUIT_TYPE_PRODUIT_NOT_FOUND"}), 404

    return jsonify(_link_out.dump(link)), 200


@produit_type_produit_bp.post("/produit-type-produits")
@jwt_required()
def post_produit_type_produit_route():
    _ = get_jwt_identity()

    payload = request.get_json(silent=True) or {}
    data = _link_create_in.load(payload)

    try:
        link = create_produit_type_produit(
            produit_id=data["produit_id"],
            type_produit_id=data["type_produit_id"],
        )
    except IntegrityError:
        # - PK composite déjà existante
        # - FK produit_id invalide
        # - FK type_produit_id invalide
        return jsonify({"ok": False, "error": "PRODUIT_TYPE_PRODUIT_CONSTRAINT"}), 409

    return jsonify(_link_out.dump(link)), 201


@produit_type_produit_bp.delete("/produit-type-produits/<int:produit_id>/<int:type_produit_id>")
@jwt_required()
def delete_produit_type_produit_route(produit_id: int, type_produit_id: int):
    _ = get_jwt_identity()

    ok = delete_produit_type_produit(produit_id, type_produit_id)
    if not ok:
        return jsonify({"ok": False, "error": "PRODUIT_TYPE_PRODUIT_NOT_FOUND"}), 404

    return jsonify(
        {"ok": True, "deleted": {"produit_id": produit_id, "type_produit_id": type_produit_id}},
    ), 200
