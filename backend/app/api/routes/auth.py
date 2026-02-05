from flask import Blueprint, request
from datetime import datetime, timezone
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
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
    try:
        user = authenticate(email=data["email"], password=data["password"])

        access = create_access_token(identity=user.id)
        refresh = create_refresh_token(identity=user.id)

        return {"access_token": access, "refresh_token": refresh, "token_type": "Bearer"}, 200
    except UnauthorizedError as e:
        return {"error": {"code": "UNAUTHORIZED", "message": str(e)}}, 401

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access = create_access_token(identity=user_id)
    return {"access_token": access, "token_type": "Bearer"}, 200

@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    if not user:
        return {"error": {"code": "NOT_FOUND", "message": "User not found"}}, 404
    return {"user": _user_out.dump(user)}, 200
@auth_bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    jwt_payload = get_jwt()
    user_id = get_jwt_identity()

    jti = jwt_payload["jti"]
    token_type = jwt_payload["type"]
    exp = jwt_payload["exp"]

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    revoke_token(jti=jti, token_type=token_type, user_id=int(user_id), expires_at=expires_at)

    return {"ok": True}, 200
