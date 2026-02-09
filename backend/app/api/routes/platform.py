from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.schemas.platform import PlatformReadSchema, PlatformFilterSchema, PlatformCreateSchema, PlatformPatchSchema
from app.crud.platform import get_platforms, get_platform_by_id, NotFoundError, create_platform, delete_platform, ConflictError, patch_platform
from flask_jwt_extended import jwt_required
platform_bp = Blueprint("platform", __name__, url_prefix="/api")

_platform_out_many = PlatformReadSchema(many=True)
_platform_out_one = PlatformReadSchema()
_filters_in = PlatformFilterSchema()
_platform_in = PlatformCreateSchema()

_platform_patch = PlatformPatchSchema()
@platform_bp.get("/platforms")
@jwt_required()
def get_platforms_route():
    raw = request.args.to_dict(flat=True)

    try:
        filters = _filters_in.load(raw)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    platforms = get_platforms(filters)
    return jsonify(_platform_out_many.dump(platforms)), 200


@platform_bp.get("/platforms/<int:platform_id>")
@jwt_required()
def get_platform_by_id_route(platform_id: int):
    try:
        platform = get_platform_by_id(platform_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Plateforme introuvable"}}, 404

    return jsonify(_platform_out_one.dump(platform)), 200

@platform_bp.post("/platforms")
@jwt_required()
def post_platform():
    try:
        data = _platform_in.load(request.get_json(force=True))
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "messages": e.messages}}, 400

    try:
        platform = create_platform(data)
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409

    return jsonify(_platform_out_one.dump(platform)), 201


@platform_bp.delete("/platforms/<int:platform_id>")
@jwt_required()
def delete_platform_route(platform_id: int):
    try:
        delete_platform(platform_id)
    except NotFoundError:
        return {"error": {"code": "NOT_FOUND", "message": "Plateforme introuvable"}}, 404

    return {"ok": True, "deleted_platform_id": platform_id}, 200

@platform_bp.patch("/platforms/<int:platform_id>")
@jwt_required()
def patch_platform_route(platform_id: int):
    data = request.get_json(silent=True) or {}

    patch = _platform_patch.load(data, partial=True)

    try:
        platform = patch_platform(platform_id, patch)
    except NotFoundError as e:
        return {"message": str(e)}, 404
    except ConflictError as e:
        return {"message": str(e)}, 409

    return jsonify(_platform_out_one.dump(platform)), 200