from flask import Blueprint, request, make_response, jsonify
from datetime import datetime, timezone
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_csrf_token
)
from app.crud.token_blocklist import revoke_token

from app.schemas.auth import RegisterSchema, LoginSchema, UserReadSchema
from app.crud.user import create_user, authenticate, ConflictError, UnauthorizedError, get_user_by_id

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

_register = RegisterSchema()
_login = LoginSchema()
_user_out = UserReadSchema()

@auth_bp.post("/register")
def register():
    data = _register.load(request.get_json(force=True))
    try:
        user = create_user(
            name=data["name"],
            email=data["email"],
            password=data["password"],
            pro=data["pro"],
        )
        return {"user": _user_out.dump(user)}, 201
    except ConflictError as e:
        return {"error": {"code": "CONFLICT", "message": str(e)}}, 409

@auth_bp.post("/login")
def login():
    data = _login.load(request.get_json(force=True))
    user = authenticate(email=data["email"], password=data["password"])

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    body = {
        "ok": True,
        "user": _user_out.dump(user),
        "csrf_access_token": get_csrf_token(access_token),
        "csrf_refresh_token": get_csrf_token(refresh_token),
    }

    response = make_response(jsonify(body), 200)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access = create_access_token(identity=str(user_id))
    resp = {"ok": True}
    response = make_response(resp, 200)
    set_access_cookies(response, access)
    resp["csrf_access_token"] = get_csrf_token(access)
    return response

@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = get_user_by_id(user_id)
    if not user:
        return {"error": {"code": "NOT_FOUND", "message": "User not found"}}, 404
    return {"user": _user_out.dump(user)}, 200
@auth_bp.post("/logout_refresh")
@jwt_required(refresh=True)
def logout_refresh():
    jwt_payload = get_jwt()
    user_id = int(get_jwt_identity())

    revoke_token(
        jti=jwt_payload["jti"],
        token_type=jwt_payload["type"],
        user_id=user_id,
        expires_at=datetime.fromtimestamp(jwt_payload["exp"], tz=timezone.utc),
    )

    response = make_response({"ok": True, "msg": "Refresh token revoked"}, 200)
    unset_jwt_cookies(response)
    return response
@auth_bp.post("/logout")
@jwt_required()
def logout():
    jwt_payload = get_jwt()
    user_id = int(get_jwt_identity())

    revoke_token(
        jti=jwt_payload["jti"],
        token_type=jwt_payload["type"],  # access
        user_id=user_id,
        expires_at=datetime.fromtimestamp(jwt_payload["exp"], tz=timezone.utc),
    )

    response = make_response({"ok": True, "msg": "Access token revoked"}, 200)
    unset_jwt_cookies(response)
    return response