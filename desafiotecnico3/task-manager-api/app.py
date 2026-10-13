import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.auth import TOKEN_SERVICE_KEY
from middlewares.error_handler import register_error_handlers
from routes.category_routes import build_category_routes
from routes.report_routes import build_report_routes
from routes.system_routes import build_system_routes
from routes.task_routes import build_task_routes
from routes.user_routes import build_user_routes
from services.notification_service import NotificationService
from services.token_service import TokenService


def create_app(settings=Settings):
    """Composition root: config, banco, serviços, controllers, rotas e handlers de erro."""
    app = Flask(__name__)
    app.config.from_object(settings)
    logging.basicConfig(level=app.config['LOG_LEVEL'], format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    CORS(app, origins=app.config['CORS_ORIGINS'])
    db.init_app(app)

    token_service = TokenService(app.config['SECRET_KEY'], app.config['TOKEN_MAX_AGE_SECONDS'])
    app.extensions[TOKEN_SERVICE_KEY] = token_service
    notifier = NotificationService.from_config(app.config)

    app.register_blueprint(build_system_routes())
    app.register_blueprint(build_task_routes(TaskController(notifier)))
    app.register_blueprint(build_user_routes(UserController(token_service)))
    app.register_blueprint(build_report_routes(ReportController()))
    app.register_blueprint(build_category_routes(CategoryController()))
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
