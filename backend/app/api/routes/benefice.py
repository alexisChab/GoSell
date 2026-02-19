from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas.benefice import *
from app.crud.benefice import *
benefice_bp = Blueprint("benefice", __name__)
_filters_in = BenefitFilterSchema()
_out_summary = BenefitSummaryReadSchema()
_whatif_in = ProductWhatIfQuerySchema()
_forecast_in = ProductForecastQuerySchema()
_risk_in = RiskProductsQuerySchema()
_risk_out = RiskProductsReadSchema()
_whatif_out = ProductWhatIfReadSchema()
_forecast_out = ProductForecastReadSchema()
_best_types_in = BestTypesQuerySchema()
_best_types_out = BestTypesReadSchema()
_breakdown_in = BenefitBreakdownQuerySchema()
_breakdown_out = BenefitBreakdownReadSchema()

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

@benefice_bp.get("/risk-products")
@jwt_required()
def get_risk_products():
    user_id = int(get_jwt_identity())

    try:
        raw = request.args.to_dict(flat=True)
        args = _risk_in.load(raw)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    data = get_risk_products_for_user(user_id=user_id, filters=args)
    return jsonify(_risk_out.dump(data)), 200

@benefice_bp.get("/best-types")
@jwt_required()
def best_types():
    user_id = int(get_jwt_identity())

    try:
        raw = request.args.to_dict(flat=True)
        args = _best_types_in.load(raw)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    data = get_best_types_for_user(user_id=user_id, filters=args)
    return jsonify(_best_types_out.dump(data)), 200

@benefice_bp.get("/benefices/breakdown")
@jwt_required()
def benefices_breakdown():
    user_id = int(get_jwt_identity())

    try:
        raw = request.args.to_dict(flat=True)
        args = _breakdown_in.load(raw)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    data = get_benefice_breakdown_for_user(user_id=user_id, filters=args)
    return jsonify(_breakdown_out.dump(data)), 200
