import logging
import secrets

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

PRODUTOS_DEMO = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Clientes de demonstração (documentados no README); só criados com SEED_DEMO_DATA=true.
CLIENTES_DEMO = [
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
]


def seed(conn, config):
    """Popula um banco vazio. Senhas são gravadas sempre com hash."""
    vazio = conn.execute(
        "SELECT (SELECT COUNT(*) FROM produtos) + (SELECT COUNT(*) FROM usuarios)"
    ).fetchone()[0] == 0
    if not vazio:
        return

    admin_password = config.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(16)
    usuarios = [("Admin", "admin@loja.com", admin_password, "admin")]

    with conn:
        if config.get("SEED_DEMO_DATA"):
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                PRODUTOS_DEMO,
            )
            usuarios += [(nome, email, senha, "cliente") for nome, email, senha in CLIENTES_DEMO]
        conn.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in usuarios],
        )

    if not config.get("SEED_ADMIN_PASSWORD"):
        logger.warning("SEED_ADMIN_PASSWORD não definida: admin@loja.com criado com senha aleatória")
