class SistemaModel:
    """Consultas de infraestrutura (health check)."""

    def __init__(self, db):
        self.db = db

    def contagens(self):
        row = self.db.execute(
            """
            SELECT (SELECT COUNT(*) FROM produtos WHERE ativo = 1) AS produtos,
                   (SELECT COUNT(*) FROM usuarios) AS usuarios,
                   (SELECT COUNT(*) FROM pedidos) AS pedidos
            """
        ).fetchone()
        return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}
