from flask import Blueprint

from src.views.response import to_response


def build_sistema_routes(controller):
    bp = Blueprint("sistema", __name__)

    bp.add_url_rule("/", "index", lambda: to_response(controller.index()), methods=["GET"])
    bp.add_url_rule("/health", "health", lambda: to_response(controller.health()), methods=["GET"])
    return bp
