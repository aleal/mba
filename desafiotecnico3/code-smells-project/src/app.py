import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database.connection import get_db, init_db
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.views.admin_routes import build_admin_routes
from src.views.pedido_routes import build_pedido_routes
from src.views.produto_routes import build_produto_routes
from src.views.sistema_routes import build_sistema_routes
from src.views.usuario_routes import build_usuario_routes


def create_app(settings=Settings):
    """Composition root: carrega config, prepara o banco e injeta as dependências."""
    app = Flask(__name__)
    app.config.from_object(settings)
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    CORS(app, origins=app.config["CORS_ORIGINS"])
    init_db(app)

    notifier = NotificationService()
    app.register_blueprint(build_sistema_routes(
        SistemaController(get_db, app.config["APP_VERSION"], app.config["APP_ENV"])))
    app.register_blueprint(build_produto_routes(ProdutoController(get_db)))
    app.register_blueprint(build_usuario_routes(UsuarioController(get_db)))
    app.register_blueprint(build_pedido_routes(PedidoController(get_db, notifier)))
    app.register_blueprint(build_admin_routes(AdminController(
        get_db, app.config["ENABLE_ADMIN_RESET"], app.config["ENABLE_ADMIN_QUERY"])))

    register_error_handlers(app)
    return app
