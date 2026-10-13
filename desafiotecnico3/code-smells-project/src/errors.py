class AppError(Exception):
    """Erro de domínio, convertido em resposta HTTP pelo handler central.

    `include_sucesso` reproduz o formato original de cada endpoint: alguns erros
    da API sempre devolveram `{"erro", "sucesso": false}` e outros só `{"erro"}`.
    """

    status_code = 400

    def __init__(self, message, status_code=None, include_sucesso=False):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.include_sucesso = include_sucesso


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404
