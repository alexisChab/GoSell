from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas.product import ProductReadSchema, ProductFilterSchema, ProductCreateSchema, ProductPatchSchema
from app.crud.product import get_products_for_user, get_product_for_user_by_id, create_product, delete_product, NotFoundError, ForbiddenError, update_product
from marshmallow import ValidationError

product_bp = Blueprint("product", __name__)

_product_out = ProductReadSchema()
_products_out = ProductReadSchema(many=True)
_filters_in = ProductFilterSchema()
_product_in = ProductCreateSchema()
_product_out = ProductReadSchema()
_patch_in = ProductPatchSchema()

@product_bp.get("/products")
@jwt_required()
def get_products():
    user_id = int(get_jwt_identity())

    raw = request.args.to_dict(flat=True)
    filters = _filters_in.load(raw)

    produits = get_products_for_user(user_id, filters)
    return jsonify(_products_out.dump(produits)), 200


@product_bp.get("/products/<int:product_id>")
@jwt_required()
def get_product(product_id: int):
    user_id = int(get_jwt_identity())

    produit = get_product_for_user_by_id(user_id, product_id)
    if not produit:
        return {"error": {"code": "NOT_FOUND", "message": "Produit introuvable"}}, 404

    return jsonify(_product_out.dump(produit)), 200

@product_bp.post("/products")
@jwt_required()
def post_product():
    user_id = int(get_jwt_identity())

    try:
        data = _product_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    produit = create_product(user_id, data)
    return jsonify(_product_out.dump(produit)), 201

@product_bp.delete("/products/<int:product_id>")
@jwt_required()
def delete_product_route(product_id: int):
    user_id = int(get_jwt_identity())

    try:
        delete_product(user_id, product_id)
    except NotFoundError:
        return {
            "error": {
                "code": "NOT_FOUND",
                "message": "Produit introuvable",
            }
        }, 404
    except ForbiddenError:
        return {
            "error": {
                "code": "FORBIDDEN",
                "message": "Accès interdit à ce produit",
            }
        }, 403
    return {
        "ok": True,
        "deleted_product_id": product_id,
    }, 200

@product_bp.patch("/products/<int:product_id>")
@jwt_required()
def patch_product(product_id: int):
    user_id = int(get_jwt_identity())

    try:
        patch_data = _patch_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    try:
        produit = update_product(user_id, product_id, patch_data)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Produit introuvable"}}, 404

    return jsonify(_product_out.dump(produit)), 200