from flask import Blueprint, request

from middlewares.auth import current_actor, require_admin
from routes import respond


def build_user_routes(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.get('/users')
    def get_users():
        return respond(controller.list_users())

    @user_bp.get('/users/<int:user_id>')
    def get_user(user_id):
        return respond(controller.get_user(user_id))

    @user_bp.post('/users')
    def create_user():
        return respond(controller.create_user(request.get_json(), actor=current_actor()))

    @user_bp.put('/users/<int:user_id>')
    def update_user(user_id):
        return respond(controller.update_user(user_id, request.get_json(), actor=current_actor()))

    @user_bp.delete('/users/<int:user_id>')
    @require_admin
    def delete_user(user_id):
        return respond(controller.delete_user(user_id))

    @user_bp.get('/users/<int:user_id>/tasks')
    def get_user_tasks(user_id):
        return respond(controller.list_user_tasks(user_id))

    @user_bp.post('/login')
    def login():
        return respond(controller.login(request.get_json()))

    return user_bp
