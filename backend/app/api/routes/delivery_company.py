from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required

from app.schemas.delivery_company import (
    DeliveryCompanyReadSchema,
    DeliveryCompanyCreateSchema,
    DeliveryCompanyPatchSchema,
)
from app.crud.delivery_company import (
    get_delivery_companies,
    get_delivery_company_by_id,
    create_delivery_company,
    patch_delivery_company,
    delete_delivery_company,
    NotFoundError,
    ConflictError,
)

delivery_company_bp = Blueprint("delivery_company", __name__, url_prefix="/api")

_dc_out_one = DeliveryCompanyReadSchema()
_dc_out_many = DeliveryCompanyReadSchema(many=True)

_dc_create_in = DeliveryCompanyCreateSchema()
_dc_patch_in = DeliveryCompanyPatchSchema()


@delivery_company_bp.get("/delivery-companies")
def get_delivery_companies_route():
    # si tu n'as pas encore FilterSchema, on supporte juste search/pagination/tri en "best effort"
    raw = request.args.to_dict(flat=True)

    filters = {
        "search": raw.get("search"),
        "order_by": raw.get("order_by", "id"),
        "order_dir": raw.get("order_dir", "asc"),
        "page": int(raw.get("page", 1)),
        "page_size": int(raw.get("page_size", 20)),
    }

    items = get_delivery_companies(filters)
    return jsonify(_dc_out_many.dump(items)), 200


@delivery_company_bp.get("/delivery-companies/<int:company_id>")
def get_delivery_company_by_id_route(company_id: int):
    try:
        item = get_delivery_company_by_id(company_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Société de livraison introuvable"}}, 404

    return jsonify(_dc_out_one.dump(item)), 200


@delivery_company_bp.post("/delivery-companies")
@jwt_required()
def post_delivery_company_route():
    try:
        data = _dc_create_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    try:
        item = create_delivery_company(data)
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409

    return jsonify(_dc_out_one.dump(item)), 201


@delivery_company_bp.patch("/delivery-companies/<int:company_id>")
@jwt_required()
def patch_delivery_company_route(company_id: int):
    payload = request.get_json(silent=True) or {}

    # PATCH partiel
    try:
        patch = _dc_patch_in.load(payload, partial=True)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    if not patch:
        return {"error": {"code": "VALIDATION_ERROR", "messages": {"_schema": ["Aucun champ fourni."]}}}, 400

    try:
        item = patch_delivery_company(company_id, patch)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Société de livraison introuvable"}}, 404
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409

    return jsonify(_dc_out_one.dump(item)), 200


@delivery_company_bp.delete("/delivery-companies/<int:company_id>")
@jwt_required()
def delete_delivery_company_route(company_id: int):
    try:
        delete_delivery_company(company_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Société de livraison introuvable"}}, 404

    return {"ok": True, "deleted_delivery_company_id": company_id}, 200
