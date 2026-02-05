
from flask_jwt_extended import JWTManager
from app.crud.token_blocklist import is_token_revoked

def register_jwt_callbacks(jwt: JWTManager):
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload) -> bool:
        return is_token_revoked(jwt_payload["jti"])

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {"error": {"code": "TOKEN_REVOKED", "message": "Token has been revoked"}}, 401
