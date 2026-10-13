from flask import Blueprint, request

from src.middlewares.auth import require_admin_token
from src.views.response import to_response


def build_admin_routes(controller):
    bp = Blueprint("admin", __name__)

    bp.add_url_rule("/admin/reset-db", "reset_db",
                    require_admin_token(lambda: to_response(controller.resetar_banco())), methods=["POST"])
    bp.add_url_rule("/admin/query", "query",
                    require_admin_token(lambda: to_response(controller.executar_query(request.get_json(silent=True)))),
                    methods=["POST"])
    return bp
