import hmac

from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"
_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")

# `senha` nunca sai do model.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def usuario_to_dict(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


class UsuarioModel:
    def __init__(self, db):
        self.db = db

    def listar(self):
        rows = self.db.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [usuario_to_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self.db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return usuario_to_dict(row) if row else None

    def existe(self, usuario_id):
        return self.db.execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, generate_password_hash(senha), tipo),
            )
        return cursor.lastrowid

    def autenticar(self, email, senha):
        """Devolve o usuário (sem senha) se as credenciais conferem, senão None."""
        rows = self.db.execute(
            "SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)
        ).fetchall()
        for row in rows:
            if self._senha_confere(row, senha):
                return usuario_to_dict(row, CAMPOS_LOGIN)
        return None

    def _senha_confere(self, row, senha):
        armazenada = row["senha"] or ""
        if armazenada.startswith(_PREFIXOS_HASH):
            return check_password_hash(armazenada, senha)
        # Senha legada em texto puro: confere e migra para hash na mesma hora.
        if hmac.compare_digest(armazenada.encode(), senha.encode()):
            with self.db:
                self.db.execute(
                    "UPDATE usuarios SET senha = ? WHERE id = ?",
                    (generate_password_hash(senha), row["id"]),
                )
            return True
        return False
