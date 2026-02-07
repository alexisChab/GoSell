from app.api.routes.health import health_bp
from app.api.routes.auth import auth_bp
from app.api.routes.product import product_bp
from app.api.routes.stock import stock_bp

def register_routes(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp, url_prefix="/api")
    app.register_blueprint(stock_bp, url_prefix="/api")
