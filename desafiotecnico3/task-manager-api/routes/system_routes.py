from datetime import datetime

from flask import Blueprint


def build_system_routes():
    system_bp = Blueprint('system', __name__)

    @system_bp.get('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    @system_bp.get('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return system_bp
