from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required

from app.schemas.category import (
    CategoryReadSchema,
    CategoryCreateSchema,
    CategoryPatchSchema,
)
from app.crud.category import (
    get_categories,
    get_category_by_id,
    create_category,
    patch_category,
    delete_category,
    NotFoundError,
    ConflictError,
)

category_bp = Blueprint("category", __name__, url_prefix="/api")

_cat_out_one = CategoryReadSchema()
_cat_out_many = CategoryReadSchema(many=True)

_cat_create_in = CategoryCreateSchema()
_cat_patch_in = CategoryPatchSchema()


@category_bp.get("/categories")
def get_categories_route():
    items = get_categories()
    return jsonify(_cat_out_many.dump(items)), 200


@category_bp.get("/categories/<int:category_id>")
def get_category_by_id_route(category_id: int):
    try:
        item = get_category_by_id(category_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Catégorie introuvable"}}, 404

    return jsonify(_cat_out_one.dump(item)), 200


@category_bp.post("/categories")
@jwt_required()
def post_category_route():
    try:
        data = _cat_create_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    try:
        item = create_category(data)
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409

    return jsonify(_cat_out_one.dump(item)), 201


@category_bp.patch("/categories/<int:category_id>")
@jwt_required()
def patch_category_route(category_id: int):
    payload = request.get_json(silent=True) or {}

    try:
        patch = _cat_patch_in.load(payload, partial=True)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    if not patch:
        return {"error": {"code": "VALIDATION_ERROR", "messages": {"_schema": ["Aucun champ fourni."]}}}, 400

    try:
        item = patch_category(category_id, patch)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Catégorie introuvable"}}, 404
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409

    return jsonify(_cat_out_one.dump(item)), 200


@category_bp.delete("/categories/<int:category_id>")
@jwt_required()
def delete_category_route(category_id: int):
    try:
        delete_category(category_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Catégorie introuvable"}}, 404

    return {"ok": True, "deleted_category_id": category_id}, 200
