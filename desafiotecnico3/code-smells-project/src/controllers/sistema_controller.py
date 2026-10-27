import logging
import sqlite3

from src.models.sistema_model import SistemaModel

logger = logging.getLogger(__name__)

ENDPOINTS_PUBLICOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class SistemaController:
    def __init__(self, get_db, versao, ambiente):
        self._get_db = get_db
        self._versao = versao
        self._ambiente = ambiente

    def index(self):
        return {"mensagem": "Bem-vindo à API da Loja", "versao": self._versao, "endpoints": ENDPOINTS_PUBLICOS}, 200

    def health(self):
        try:
            contagens = SistemaModel(self._get_db()).contagens()
        except sqlite3.Error:
            logger.exception("health check: banco indisponível")
            return {"status": "erro", "detalhes": "Banco de dados indisponível"}, 500
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": self._versao,
            "ambiente": self._ambiente,
        }, 200
