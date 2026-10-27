from functools import wraps

from flask import current_app, request

from middlewares.error_handler import ForbiddenError, UnauthorizedError
from models.user import User

TOKEN_SERVICE_KEY = 'token_service'


def current_actor():
    """Usuário ativo autenticado pelo header `Authorization: Bearer <token>`, ou None."""
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return None
    user_id = current_app.extensions[TOKEN_SERVICE_KEY].verify(token.strip())
    if user_id is None:
        return None
    user = User.get_by_id(user_id)
    return user if user and user.active else None


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        actor = current_actor()
        if actor is None:
            raise UnauthorizedError('Token inválido ou ausente')
        if not actor.is_admin():
            raise ForbiddenError('Acesso restrito a administradores')
        return view(*args, **kwargs)
    return wrapper
