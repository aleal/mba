from flask import Blueprint, request

from middlewares.auth import require_admin
from routes import respond


def build_category_routes(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.get('/categories')
    def get_categories():
        return respond(controller.list_categories())

    @category_bp.post('/categories')
    def create_category():
        return respond(controller.create_category(request.get_json()))

    @category_bp.put('/categories/<int:cat_id>')
    def update_category(cat_id):
        return respond(controller.update_category(cat_id, request.get_json()))

    @category_bp.delete('/categories/<int:cat_id>')
    @require_admin
    def delete_category(cat_id):
        return respond(controller.delete_category(cat_id))

    return category_bp
