import logging

from src.controllers.validators import is_positive_int, require_dict
from src.errors import NotFoundError, ValidationError
from src.models.pedido_model import STATUS_VALIDOS, PedidoModel
from src.models.usuario_model import UsuarioModel

logger = logging.getLogger(__name__)


def validar_itens(itens):
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise ValidationError("Itens devem ser uma lista")
    for item in itens:
        if not (
            isinstance(item, dict)
            and is_positive_int(item.get("produto_id"))
            and is_positive_int(item.get("quantidade"))
        ):
            raise ValidationError("Item inválido: produto_id e quantidade devem ser inteiros positivos")
    return itens


class PedidoController:
    def __init__(self, get_db, notifier):
        self._get_db = get_db
        self._notifier = notifier

    def criar(self, dados):
        require_dict(dados)
        usuario_id = dados.get("usuario_id")
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not is_positive_int(usuario_id):
            raise ValidationError("Usuario ID inválido")
        itens = validar_itens(dados.get("itens", []))

        db = self._get_db()
        if not UsuarioModel(db).existe(usuario_id):
            raise ValidationError("Usuário não encontrado", include_sucesso=True)
        resultado = PedidoModel(db).criar(usuario_id, itens)

        self._notifier.pedido_criado(resultado["pedido_id"], usuario_id)
        return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201

    def listar_todos(self):
        return {"dados": PedidoModel(self._get_db()).listar(), "sucesso": True}, 200

    def listar_por_usuario(self, usuario_id):
        return {"dados": PedidoModel(self._get_db()).listar(usuario_id=usuario_id), "sucesso": True}, 200

    def atualizar_status(self, pedido_id, dados):
        novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")

        model = PedidoModel(self._get_db())
        if not model.existe(pedido_id):
            raise NotFoundError("Pedido não encontrado")
        model.atualizar_status(pedido_id, novo_status)

        self._notifier.status_pedido_alterado(pedido_id, novo_status)
        return {"sucesso": True, "mensagem": "Status atualizado"}, 200

    def relatorio_vendas(self):
        return {"dados": PedidoModel(self._get_db()).relatorio_vendas(), "sucesso": True}, 200
