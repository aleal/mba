from flask import Blueprint, request

from src.views.response import to_response


def build_pedido_routes(controller):
    bp = Blueprint("pedidos", __name__)

    bp.add_url_rule("/pedidos", "criar",
                    lambda: to_response(controller.criar(request.get_json(silent=True))), methods=["POST"])
    bp.add_url_rule("/pedidos", "listar_todos", lambda: to_response(controller.listar_todos()), methods=["GET"])
    bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_por_usuario",
                    lambda usuario_id: to_response(controller.listar_por_usuario(usuario_id)), methods=["GET"])
    bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status",
                    lambda pedido_id: to_response(controller.atualizar_status(pedido_id, request.get_json(silent=True))),
                    methods=["PUT"])
    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas",
                    lambda: to_response(controller.relatorio_vendas()), methods=["GET"])
    return bp
