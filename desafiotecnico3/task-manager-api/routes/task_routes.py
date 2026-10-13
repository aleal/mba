from flask import Blueprint, request

from routes import respond


def build_task_routes(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.get('/tasks')
    def get_tasks():
        return respond(controller.list_tasks())

    @task_bp.get('/tasks/<int:task_id>')
    def get_task(task_id):
        return respond(controller.get_task(task_id))

    @task_bp.post('/tasks')
    def create_task():
        return respond(controller.create_task(request.get_json()))

    @task_bp.put('/tasks/<int:task_id>')
    def update_task(task_id):
        return respond(controller.update_task(task_id, request.get_json()))

    @task_bp.delete('/tasks/<int:task_id>')
    def delete_task(task_id):
        return respond(controller.delete_task(task_id))

    @task_bp.get('/tasks/search')
    def search_tasks():
        return respond(controller.search_tasks(request.args))

    @task_bp.get('/tasks/stats')
    def task_stats():
        return respond(controller.stats())

    return task_bp
