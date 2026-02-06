from flask import Flask
from flask_cors import CORS
from app.api.routes import register_routes
from dotenv import load_dotenv
from marshmallow import ValidationError
from app.db.request_session import init_request_db
from app.config import Config
from app.extensions import jwt
from app.jwt_callbacks import register_jwt_callbacks
from app.crud.user import AppError
from app.crud.token_blocklist import is_token_revoked

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    init_request_db(app)
    jwt.init_app(app)
    register_jwt_callbacks(jwt)

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        # e.messages = dict field -> list[str]
        return {"error": {"code": "VALIDATION_ERROR", "message": "Invalid payload", "details": e.messages}}, 400

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_token_revoked(jwt_payload["jti"])

    @app.errorhandler(AppError)
    def handle_app_error(e: AppError):
        status = 400
        if e.code == "UNAUTHORIZED":
            status = 401
        elif e.code == "CONFLICT":
            status = 409
        elif e.code == "NOT_FOUND":
            status = 404

        return {"error": {"code": e.code, "message": e.message}}, status
    register_routes(app)
    return app
