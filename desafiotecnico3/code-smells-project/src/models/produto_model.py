CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN, NOME_MAX = 2, 200

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def produto_to_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


class ProdutoModel:
    def __init__(self, db):
        self.db = db

    def listar(self):
        rows = self.db.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY id").fetchall()
        return [produto_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self.db.execute(
            "SELECT * FROM produtos WHERE id = ? AND ativo = 1", (produto_id,)
        ).fetchone()
        return produto_to_dict(row) if row else None

    def buscar_por_ids(self, produto_ids):
        """Produtos ativos indexados por id, em uma única query."""
        if not produto_ids:
            return {}
        placeholders = ", ".join("?" for _ in produto_ids)
        rows = self.db.execute(
            f"SELECT * FROM produtos WHERE ativo = 1 AND id IN ({placeholders})",
            tuple(produto_ids),
        ).fetchall()
        return {row["id"]: row for row in rows}

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clauses, params = ["ativo = 1"], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            params.append(preco_max)
        rows = self.db.execute(
            f"SELECT * FROM produtos WHERE {' AND '.join(clauses)} ORDER BY id", params
        ).fetchall()
        return [produto_to_dict(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        with self.db:
            self.db.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def desativar(self, produto_id):
        """Exclusão lógica: preserva o vínculo com itens de pedidos já feitos."""
        with self.db:
            self.db.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,))
