from flask import Blueprint, request

from src.views.response import to_response


def build_usuario_routes(controller):
    bp = Blueprint("usuarios", __name__)

    bp.add_url_rule("/usuarios", "listar", lambda: to_response(controller.listar()), methods=["GET"])
    bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar",
                    lambda usuario_id: to_response(controller.buscar(usuario_id)), methods=["GET"])
    bp.add_url_rule("/usuarios", "criar",
                    lambda: to_response(controller.criar(request.get_json(silent=True))), methods=["POST"])
    bp.add_url_rule("/login", "login",
                    lambda: to_response(controller.login(request.get_json(silent=True))), methods=["POST"])
    return bp
