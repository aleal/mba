import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        body = {"erro": err.message}
        if err.include_sucesso:
            body["sucesso"] = False
        return jsonify(body), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return err  # 404/405 do roteamento mantêm a resposta padrão do Flask

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
