from src.errors import ValidationError
from src.models.produto_model import ProdutoModel

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
PRODUTO_DESCONHECIDO = "Desconhecido"


def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0


def calcular_total(itens, produtos):
    total = 0
    for item in itens:
        total += produtos[item["produto_id"]]["preco"] * item["quantidade"]
    return total


class PedidoModel:
    def __init__(self, db):
        self.db = db

    def criar(self, usuario_id, itens):
        """Cria pedido, itens e baixa de estoque em uma única transação."""
        produtos = ProdutoModel(self.db).buscar_por_ids({item["produto_id"] for item in itens})
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado", include_sucesso=True)
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}", include_sucesso=True)

        total = calcular_total(itens, produtos)
        with self.db:  # commit no fim, rollback em qualquer exceção
            pedido_id = self.db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            ).lastrowid
            for item in itens:
                produto = produtos[item["produto_id"]]
                self.db.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
                )
                baixa = self.db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if baixa.rowcount == 0:
                    raise ValidationError(f"Estoque insuficiente para {produto['nome']}", include_sucesso=True)
        return {"pedido_id": pedido_id, "total": total}

    def listar(self, usuario_id=None):
        """Pedidos com itens e nome do produto em uma única query (sem N+1)."""
        sql = """
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
                   pr.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido i ON i.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = i.produto_id
        """
        params = ()
        if usuario_id is not None:
            sql += " WHERE p.usuario_id = ?"
            params = (usuario_id,)
        sql += " ORDER BY p.id, i.id"

        pedidos = {}
        for row in self.db.execute(sql, params).fetchall():
            pedido = pedidos.setdefault(row["id"], {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            })
            if row["item_id"] is not None:
                pedido["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or PRODUTO_DESCONHECIDO,
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())

    def existe(self, pedido_id):
        return self.db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None

    def atualizar_status(self, pedido_id, novo_status):
        with self.db:
            self.db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))

    def relatorio_vendas(self):
        row = self.db.execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(status = ?), 0) AS pendentes,
                   COALESCE(SUM(status = ?), 0) AS aprovados,
                   COALESCE(SUM(status = ?), 0) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        total_pedidos, faturamento = row["total_pedidos"], row["faturamento"]
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": row["pendentes"],
            "pedidos_aprovados": row["aprovados"],
            "pedidos_cancelados": row["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
