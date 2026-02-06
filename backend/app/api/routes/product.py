from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas.product import ProductReadSchema, ProductFilterSchema
from app.crud.product import get_products_for_user, get_product_for_user_by_id

product_bp = Blueprint("product", __name__)

_product_out = ProductReadSchema()
_products_out = ProductReadSchema(many=True)
_filters_in = ProductFilterSchema()


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