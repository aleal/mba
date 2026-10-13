from itsdangerous import BadSignature, URLSafeTimedSerializer


class TokenService:
    """Tokens de login assinados com a SECRET_KEY e com validade (itsdangerous já vem com o Flask)."""

    _SALT = 'task-manager-auth'

    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=self._SALT)
        self._max_age = max_age_seconds

    def issue(self, user_id):
        return self._serializer.dumps({'uid': user_id})

    def verify(self, token):
        """Devolve o id do usuário, ou None se o token for inválido ou estiver expirado."""
        try:
            return self._serializer.loads(token, max_age=self._max_age).get('uid')
        except (BadSignature, AttributeError):
            return None
