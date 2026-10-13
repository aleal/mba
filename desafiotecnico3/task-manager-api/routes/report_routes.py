from flask import Blueprint

from routes import respond


def build_report_routes(controller):
    report_bp = Blueprint('reports', __name__)

    @report_bp.get('/reports/summary')
    def summary_report():
        return respond(controller.summary())

    @report_bp.get('/reports/user/<int:user_id>')
    def user_report(user_id):
        return respond(controller.user_report(user_id))

    return report_bp
