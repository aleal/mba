import logging
import sqlite3

from src.errors import ForbiddenError, ValidationError
from src.models.admin_model import AdminModel

logger = logging.getLogger(__name__)


class AdminController:
    """Casos de uso administrativos. A autenticação é feita pelo middleware;
    aqui ficam as flags que mantêm as operações desligadas por padrão."""

    def __init__(self, get_db, reset_habilitado, query_habilitada):
        self._get_db = get_db
        self._reset_habilitado = reset_habilitado
        self._query_habilitada = query_habilitada

    def resetar_banco(self):
        if not self._reset_habilitado:
            raise ForbiddenError("Endpoint desabilitado")
        AdminModel(self._get_db()).resetar()
        logger.warning("banco de dados resetado via /admin/reset-db")
        return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200

    def executar_query(self, dados):
        if not self._query_habilitada:
            raise ForbiddenError("Endpoint desabilitado")
        sql = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not isinstance(sql, str) or not sql.strip():
            raise ValidationError("Query não informada")
        if not sql.lstrip().upper().startswith("SELECT"):
            raise ValidationError("Apenas consultas SELECT são permitidas")
        try:
            resultado = AdminModel(self._get_db()).consultar_somente_leitura(sql)
        except sqlite3.Error:
            logger.warning("consulta administrativa rejeitada", exc_info=True)
            raise ValidationError("Consulta inválida") from None
        logger.info("consulta administrativa executada linhas=%d", len(resultado))
        return {"dados": resultado, "sucesso": True}, 200
