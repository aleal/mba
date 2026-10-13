from flask import Blueprint, request

from src.views.response import to_response


def build_produto_routes(controller):
    bp = Blueprint("produtos", __name__)

    bp.add_url_rule("/produtos", "listar", lambda: to_response(controller.listar()), methods=["GET"])
    bp.add_url_rule("/produtos/busca", "pesquisar", lambda: to_response(controller.pesquisar(request.args)), methods=["GET"])
    bp.add_url_rule("/produtos/<int:produto_id>", "buscar",
                    lambda produto_id: to_response(controller.buscar(produto_id)), methods=["GET"])
    bp.add_url_rule("/produtos", "criar",
                    lambda: to_response(controller.criar(request.get_json(silent=True))), methods=["POST"])
    bp.add_url_rule("/produtos/<int:produto_id>", "atualizar",
                    lambda produto_id: to_response(controller.atualizar(produto_id, request.get_json(silent=True))),
                    methods=["PUT"])
    bp.add_url_rule("/produtos/<int:produto_id>", "deletar",
                    lambda produto_id: to_response(controller.deletar(produto_id)), methods=["DELETE"])
    return bp
