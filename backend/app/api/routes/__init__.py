from app.api.routes.health import health_bp
from app.api.routes.auth import auth_bp

def register_routes(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
