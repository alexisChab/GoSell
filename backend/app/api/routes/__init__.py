from app.api.routes.health import health_bp
from app.api.routes.auth import auth_bp
from app.api.routes.product import product_bp
from app.api.routes.stock import stock_bp
from app.api.routes.platform import platform_bp
from app.api.routes.delivery_company import delivery_company_bp
from app.api.routes.categorie import category_bp
from app.api.routes.genre import genre_bp
from app.api.routes.product_type import product_type_bp
from app.api.routes.produit_type_produit import produit_type_produit_bp
from app.api.routes.where_sell import where_sell_bp
from app.api.routes.lot import lot_bp


def register_routes(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp, url_prefix="/api")
    app.register_blueprint(stock_bp, url_prefix="/api")
    app.register_blueprint(platform_bp, url_prefix="/api")
    app.register_blueprint(delivery_company_bp, url_prefix="/api")
    app.register_blueprint(category_bp, url_prefix="/api")
    app.register_blueprint(genre_bp, url_prefix="/api")
    app.register_blueprint(product_type_bp, url_prefix="/api")
    app.register_blueprint(produit_type_produit_bp, url_prefix="/api")
    app.register_blueprint(where_sell_bp, url_prefix="/api")
    app.register_blueprint(lot_bp, url_prefix="/api")