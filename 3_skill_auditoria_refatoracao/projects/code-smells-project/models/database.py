import logging
import secrets
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

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

USUARIOS_DEMO = [
    ("Admin", "admin@loja.com", "admin"),
    ("João Silva", "joao@email.com", "cliente"),
    ("Maria Santos", "maria@email.com", "cliente"),
]

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """Uma conexão por contexto de aplicação/request, fechada no teardown."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    conn = connect(app.config["DATABASE_PATH"])
    try:
        criar_schema(conn)
        migrar_senhas_em_texto(conn)
        if app.config["SEED_DEMO_DATA"]:
            semear_dados_demo(conn, app.config["SEED_USER_PASSWORD"])
    finally:
        conn.close()


def criar_schema(conn):
    with conn:
        for ddl in SCHEMA:
            conn.execute(ddl)


def semear_dados_demo(conn, senha_demo):
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    with conn:
        conn.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_DEMO,
        )
        # Sem SEED_USER_PASSWORD, cada conta demo recebe senha aleatória não divulgada.
        conn.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [
                (nome, email, generate_password_hash(senha_demo or secrets.token_urlsafe(16)), tipo)
                for nome, email, tipo in USUARIOS_DEMO
            ],
        )


def migrar_senhas_em_texto(conn):
    """Converte senhas legadas em texto puro para hash."""
    rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    legadas = [row for row in rows if row["senha"] and not row["senha"].startswith(PREFIXOS_HASH)]
    if not legadas:
        return
    with conn:
        conn.executemany(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            [(generate_password_hash(row["senha"]), row["id"]) for row in legadas],
        )
    logger.info("%d senha(s) legada(s) migrada(s) para hash.", len(legadas))


def resetar_dados():
    db = get_db()
    with db:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            db.execute(f"DELETE FROM {tabela}")
