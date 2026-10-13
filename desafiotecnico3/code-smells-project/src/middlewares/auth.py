import hmac
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError

ADMIN_TOKEN_HEADER = "X-Admin-Token"


def require_admin_token(view):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, nega sempre."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        provided = request.headers.get(ADMIN_TOKEN_HEADER, "")
        if not expected or not hmac.compare_digest(provided.encode(), expected.encode()):
            raise ForbiddenError("Acesso administrativo negado")
        return view(*args, **kwargs)

    return wrapper
