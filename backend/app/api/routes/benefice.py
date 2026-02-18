from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas.benefice import BenefitFilterSchema, BenefitSummaryReadSchema, ProductWhatIfQuerySchema, ProductForecastQuerySchema, ProductWhatIfReadSchema, ProductForecastReadSchema
from app.crud.benefice import get_benefice_summary_for_user, get_product_whatif_for_user, get_product_forecast_for_user
benefice_bp = Blueprint("benefice", __name__)
_filters_in = BenefitFilterSchema()
_out_summary = BenefitSummaryReadSchema()
_whatif_in = ProductWhatIfQuerySchema()
_forecast_in = ProductForecastQuerySchema()

_whatif_out = ProductWhatIfReadSchema()
_forecast_out = ProductForecastReadSchema()

@benefice_bp.get("/benefices")
@jwt_required()
def get_benefices_summary():
    user_id = int(get_jwt_identity())

    # ---- Validation query params ----
    try:
        raw = request.args.to_dict(flat=True)
        filters = _filters_in.load(raw)
    except ValidationError as e:
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "messages": e.messages,
            }
        }, 400

    # ---- Appel CRUD ----
    data = get_benefice_summary_for_user(user_id=user_id, filters=filters)

    return jsonify(_out_summary.dump(data)), 200
@benefice_bp.get("/products/<int:product_id>/whatif")
@jwt_required()
def product_whatif(product_id: int):
    user_id = int(get_jwt_identity())

    # ---- Validation query params ----
    try:
        raw = request.args.to_dict(flat=True)
        args = _whatif_in.load(raw)
    except ValidationError as e:
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "messages": e.messages,
            }
        }, 400

    data = get_product_whatif_for_user(
        user_id=user_id,
        product_id=product_id,
        offer_price=args["offer_price"],
    )

    if data is None:
        return {
            "error": {
                "code": "NOT_FOUND",
                "message": "Produit introuvable",
            }
        }, 404

    return jsonify(_whatif_out.dump(data)), 200

@benefice_bp.get("/products/<int:product_id>/forecast")
@jwt_required()
def product_forecast(product_id: int):
    user_id = int(get_jwt_identity())

    # ---- Validation query params ----
    try:
        raw = request.args.to_dict(flat=True)
        args = _forecast_in.load(raw)
    except ValidationError as e:
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "messages": e.messages,
            }
        }, 400

    data = get_product_forecast_for_user(
        user_id=user_id,
        product_id=product_id,
        offer_price=args.get("offer_price"),
        haircut_percent=args.get("haircut_percent"),
    )

    if data is None:
        return {
            "error": {
                "code": "NOT_FOUND",
                "message": "Produit introuvable",
            }
        }, 404

    return jsonify(_forecast_out.dump(data)), 200
