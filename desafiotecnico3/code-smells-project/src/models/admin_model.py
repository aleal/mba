class AdminModel:
    """Operações administrativas sobre o banco. O acesso é controlado nas camadas acima."""

    TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")  # filhos antes dos pais

    def __init__(self, db):
        self.db = db

    def resetar(self):
        with self.db:
            for tabela in self.TABELAS_RESET:
                self.db.execute(f"DELETE FROM {tabela}")  # nomes fixos da whitelist acima

    def consultar_somente_leitura(self, sql):
        """Executa uma única instrução com o SQLite em modo somente leitura."""
        self.db.execute("PRAGMA query_only = ON")
        try:
            rows = self.db.execute(sql).fetchall()
        finally:
            self.db.execute("PRAGMA query_only = OFF")
        return [dict(row) for row in rows]
