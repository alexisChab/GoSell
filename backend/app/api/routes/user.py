# app/api/routes/user.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.schemas.user import UserMeSchema, UserPatchMeSchema, UserPatchPasswordSchema
from app.schemas.auth import UserReadSchema  # si tu veux réutiliser le output existant
from app.crud.user import (
    get_user_by_id,
    update_user_profile,
    change_password,
    ConflictError,
    UnauthorizedError,
)

user_bp = Blueprint("user", __name__)

_me_out = UserMeSchema()
_patch_me = UserPatchMeSchema()
_patch_pwd = UserPatchPasswordSchema()


@user_bp.get("/users/me")
@jwt_required()
def get_me_route():
    user_id = int(get_jwt_identity())
    user = get_user_by_id(user_id)
    if not user:
        return {"error": {"code": "NOT_FOUND", "message": "User not found"}}, 404
    return {"user": _me_out.dump(user)}, 200


@user_bp.patch("/users/me")
@jwt_required()
def patch_me_route():
    user_id = int(get_jwt_identity())
    data = _patch_me.load(request.get_json(force=True) or {})

    try:
        user = update_user_profile(
            user_id,
            name=data.get("name"),
            username=data.get("username"),
            email=data.get("email"),
            pro=data.get("pro"),
        )
        return {"user": _me_out.dump(user)}, 200
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409


@user_bp.patch("/users/me/password")
@jwt_required()
def patch_password_route():
    user_id = int(get_jwt_identity())
    data = _patch_pwd.load(request.get_json(force=True) or {})

    try:
        change_password(
            user_id,
            current_password=data["current_password"],
            new_password=data["new_password"],
        )
        return {"ok": True}, 200
    except UnauthorizedError as e:
        return {"error": {"code": "UNAUTHORIZED", "message": str(e)}}, 401
