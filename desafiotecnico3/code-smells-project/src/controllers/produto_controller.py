import logging

from src.controllers.validators import is_int, is_number, optional_float, require_dict
from src.errors import NotFoundError, ValidationError
from src.models.produto_model import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_MAX,
    NOME_MIN,
    ProdutoModel,
)

logger = logging.getLogger(__name__)


def validar_produto(dados):
    """Validação única para criar e atualizar. Devolve os campos normalizados."""
    require_dict(dados)
    for campo, rotulo in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not is_int(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


class ProdutoController:
    def __init__(self, get_db):
        self._get_db = get_db

    def _model(self):
        return ProdutoModel(self._get_db())

    def _garantir_existe(self, model, produto_id, include_sucesso=False):
        produto = model.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado", include_sucesso=include_sucesso)
        return produto

    def listar(self):
        produtos = self._model().listar()
        logger.info("listando %d produtos", len(produtos))
        return {"dados": produtos, "sucesso": True}, 200

    def buscar(self, produto_id):
        produto = self._garantir_existe(self._model(), produto_id, include_sucesso=True)
        return {"dados": produto, "sucesso": True}, 200

    def pesquisar(self, args):
        resultados = self._model().pesquisar(
            termo=args.get("q", ""),
            categoria=args.get("categoria") or None,
            preco_min=optional_float(args.get("preco_min"), "preco_min"),
            preco_max=optional_float(args.get("preco_max"), "preco_max"),
        )
        return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200

    def criar(self, dados):
        campos = validar_produto(dados)
        produto_id = self._model().criar(**campos)
        logger.info("produto criado id=%s", produto_id)
        return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201

    def atualizar(self, produto_id, dados):
        model = self._model()
        self._garantir_existe(model, produto_id)
        campos = validar_produto(dados)
        model.atualizar(produto_id, **campos)
        return {"sucesso": True, "mensagem": "Produto atualizado"}, 200

    def deletar(self, produto_id):
        model = self._model()
        self._garantir_existe(model, produto_id)
        model.desativar(produto_id)
        logger.info("produto desativado id=%s", produto_id)
        return {"sucesso": True, "mensagem": "Produto deletado"}, 200
