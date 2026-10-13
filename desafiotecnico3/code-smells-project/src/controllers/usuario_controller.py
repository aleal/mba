import logging

from src.controllers.validators import require_dict
from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models.usuario_model import UsuarioModel

logger = logging.getLogger(__name__)


def _texto(dados, campo):
    valor = dados.get(campo, "") if isinstance(dados, dict) else ""
    return valor if isinstance(valor, str) else ""


class UsuarioController:
    def __init__(self, get_db):
        self._get_db = get_db

    def _model(self):
        return UsuarioModel(self._get_db())

    def listar(self):
        return {"dados": self._model().listar(), "sucesso": True}, 200

    def buscar(self, usuario_id):
        usuario = self._model().buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return {"dados": usuario, "sucesso": True}, 200

    def criar(self, dados):
        require_dict(dados)
        nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        usuario_id = self._model().criar(nome, email, senha)
        logger.info("usuario criado id=%s", usuario_id)
        return {"dados": {"id": usuario_id}, "sucesso": True}, 201

    def login(self, dados):
        email, senha = _texto(dados, "email"), _texto(dados, "senha")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        usuario = self._model().autenticar(email, senha)
        if usuario is None:
            logger.info("login falhou")
            raise UnauthorizedError("Email ou senha inválidos", include_sucesso=True)
        logger.info("login ok usuario=%s", usuario["id"])
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
